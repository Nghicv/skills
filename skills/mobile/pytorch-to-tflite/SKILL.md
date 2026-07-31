---
name: pytorch-to-tflite
description: Convert any PyTorch/HuggingFace model to TFLite for an Android app, quantise it, host it, and verify it on a device. Use when a feature needs an on-device model that only exists as PyTorch/ONNX/Core ML — porting an iOS Core ML model to Android, "convert model sang tflite", "chuyển model qua android", segmentation/depth/enhancement/classification models — or when a converted model runs but its output looks wrong.
---

# PyTorch → TFLite for Android

## Overview

Getting a model onto Android is four separate problems, and the last two are where the time goes:
**convert**, **shrink**, **publish**, **verify on a device**. A converted model that loads and
returns a correctly-shaped tensor is not a working model — the failure mode is silent output that
looks plausible and is wrong.

Work in this order. Do not skip step 0.

## 0. Pin down the contract, before converting

Six things decide whether the port works. Write them down for *this* model before touching a
converter; guessing any of them produces output that looks like output.

| | How to find it |
|---|---|
| Input size + layout | The reference implementation's config, HF `preprocessor_config.json`, or the ONNX/Core ML input spec. Do not assume 224 — it varies wildly (518, 384, 1024, non-square). |
| Preprocessing | `preprocessor_config.json` (`do_rescale`, `image_mean`, `image_std`, `do_pad`, `keep_aspect_ratio`), or the reference code's transform. Resize-with-padding is common and is *not* the same as a stretch. |
| What the output means | Logits? probabilities? a normalised map? metric units? relative-inverse anything? |
| Post-processing already in the graph | See below — often the surprise. |
| Reference output for one known input | One image/tensor from the reference implementation. Worth more than any amount of reading. |
| Licence of the *compiled asset* | Not the repo metadata. See below. |

**Post-processing baked into the reference graph.** Converters export the graph you give them, so
whatever the reference model does *inside* itself has to be reproduced outside — or you must
reproduce it in the wrapper. Core ML packages are protobuf; grep the op names:

```bash
unzip -q Model.mlpackage.zip -d pkg
python3 - <<'PY'
import re
d = open('pkg/Model.mlpackage/Data/com.apple.CoreML/model.mlmodel','rb').read()
print(sorted({o.decode() for o in re.findall(
    rb'(reduce_min|reduce_max|real_div|sub|clip|relu|sigmoid|softmax|argmax|scale|normalize|resize)', d)}))
PY
```

For ONNX: `onnx.load(...).graph.node[-8:]` and read the op types. Examples of what turns up, and
what it means for the Android side:

- `relu -> reduce_max -> real_div` — the output is `max(v,0)/max(v)`, a per-image divide by the
  maximum. **Not** a min..max stretch; get it wrong and the low end of the range is off.
- `sigmoid` / `softmax` at the tail — the reference emits probabilities; a raw export emits logits.
- `argmax` — the reference emits a class map; a raw export emits per-class scores.

**Licence.** A model card can say `license: mit` in its frontmatter while its License section puts
the compiled `.tflite` under a proprietary licence — Qualcomm AI Hub does exactly this. Compiled
artefacts are licensed separately from weights. Read the section, not the metadata.

## 1. Convert

**Use `litert-torch` (formerly `ai-edge-torch`), from PyTorch.** Do not route through ONNX:

- `onnx2tf` fails on transformer/ViT graphs — it mis-transposes the MLP bias adds
  (`Dimensions must be equal, but are 384 and 1536`), and fixing that means hand-writing a
  parameter-replacement JSON per block.
- ONNX exports from `onnx-community` often carry fused `com.microsoft.MultiHeadAttention`, which
  no TF converter implements.

Needs Python 3.10–3.12. If the machine has an older one, build a **self-contained** environment in
a scratch directory rather than touching the system Python — and delete it afterwards, it is ~3.5 GB:

```bash
curl -sL -o py.tar.gz https://github.com/astral-sh/python-build-standalone/releases/download/<tag>/cpython-3.11.<x>+<tag>-aarch64-apple-darwin-install_only.tar.gz
tar xzf py.tar.gz && ./python/bin/python3 -m venv venv
./venv/bin/pip install litert-torch transformers pillow ai-edge-quantizer
```

[references/convert.py](references/convert.py) takes the model id, the input shape and the output
field on the command line. Two things it does that matter for every model:

- **Wraps the module** so the graph is plain tensors in, plain tensors out. HF models return output
  objects, and multi-output models need you to choose.
- **Traces at a fixed shape.** Dynamic shapes complicate the Android side for no benefit; export one
  shape per resolution you actually need.

If tracing fails on a model that uses control flow or unsupported ops, the ladder is: patch the
wrapper to avoid the op → `torch.export` with `strict=False` → ONNX Runtime Mobile or MediaPipe
instead of TFLite → run it server-side. Do not spend a day on a converter that has already said no.

## 2. Shrink

`ai-edge-quantizer` has no float16 recipe. **Weight-only int8** is usually the right one: fp32 in
and out, so the Android side does not change at all.
[references/quantize.py](references/quantize.py) takes the recipe as an argument —
`weight_only_wi8_afp32` to start, `dynamic_wi8_afp32` if inference speed matters more than fidelity.

Measure the cost rather than assuming it. Compare the quantised output against the fp32 output on
the same input and report the number: on one depth model, 99 MB → 26 MB moved the output by a mean
of 0.9/255, i.e. invisible. On a classifier, compare top-1 agreement instead. Quantise only after
the fp32 model is verified, and verify again after.

## 3. Verify locally, then on the device

Locally first, it is a faster loop. Run the interpreter on **real input, not a synthetic gradient**
— synthetic inputs hide preprocessing mistakes — and *look at the result*.
[references/check.py](references/check.py) prints shapes, dtypes and ranges, and renders the output
according to its shape: a single-channel map as a normalised image, three channels as RGB, per-class
scores as an argmax palette.

**Preprocessing is a property of the converted file, not of the model family.** Some builds bake
the normalisation into the graph and want plain 0..1; others expect it applied up front. The wrong
choice returns an output of the right shape that has nothing to do with the input. Run both, compare
by eye — the difference is unmistakable — then make the choice **remote-config driven** in the app,
because it belongs to whichever file is published, not to the app version.

Then on a real device, because CPU/XNNPACK behaviour and timing are what ships:

- Read tensor shapes and dtypes **from the interpreter**, never hardcode, and log them.
- Write outputs somewhere you can see them: the app's external files dir for `adb pull`, and
  MediaStore (`Pictures/<Feature>`) for image-like output, so it survives an uninstall and can be
  looked at on the phone.
- Run with **`am instrument`**, not `connectedAndroidTest`: Gradle uninstalls the app afterwards,
  taking any side-loaded model and every output file with it.
- A test cannot read `/data/local/tmp` directly. Stream a pushed file in through the instrumentation
  shell: `uiAutomation.executeShellCommand("cat /data/local/tmp/model.tflite")` → copy to `filesDir`.
- Log the inference time. If it is too slow, try the GPU delegate or NNAPI before touching the model.

**Assert something semantic, and scale-free.** "The output has range" passes on noise. Pick an
invariant that survives a model swap:

| Model kind | A useful assertion |
|---|---|
| Segmentation / matting | The mask covers a plausible fraction of a known image, and the subject's pixels score higher than the background's |
| Depth | Foreground pixels drive the effect more than background ones — e.g. the near decile changes more than a flat-depth baseline, the far decile less |
| Enhancement / style | Output differs from input, correlates with it (no drift to grey), and stays in range |
| Classification / detection | Top-1 or top-k agrees with the reference on a handful of fixtures |

Avoid ratios and absolute thresholds tuned to the current model's output scale: they encode today's
model and go red when you *fix* something. (A near/far depth ratio did exactly that.)

## 4. Publish

Host the file and point remote config at it; download once into `filesDir` and cache. Prefer a URL
over bundling — an asset is dead weight in the APK for something that will be replaced, and a large
blob committed for a few weeks stays in git history forever.

Support both sources during the handover: `filesDir` → bundled asset → download. Deleting the asset
then switches everything over with no code change.

**Serve uncompressed.** Quantised weights are near-incompressible (int8 weights gzip by ~14%) — not
worth a `.zip` the app has to unpack. If bandwidth matters, use `Content-Encoding: gzip` on the
object so the HTTP client decompresses transparently:

```bash
gzip -9 -k model.tflite
gsutil -h "Content-Encoding:gzip" -h "Content-Type:application/octet-stream" \
  cp model.tflite.gz gs://<bucket>/tflite/model.tflite
```

## Android-side contract

Make the runner tolerant of how the model was converted, so a re-convert does not need an app
release:

- Read the input layout from `interpreter.getInputTensor(0).shape()` and handle both `[1,h,w,c]` and
  `[1,c,h,w]`, `FLOAT32` and `UINT8`.
- Reduce the output shape by dropping dimensions of 1, so `[1,h,w]`, `[1,h,w,1]` and `[1,1,h,w]` all
  work.
- `interpreter.run()` leaves the output buffer's position where it finished writing — **rewind before
  taking a float view**, or you read past the data and get nothing.
- Fail soft everywhere: no model, no network, an unexpected layout → return null and let the caller
  fall back to whatever it does without the model. Set an `unavailable` flag so a missing model is
  not retried on every frame.
- Cache the result against whatever the model consumed, not against the UI state, so unrelated
  changes do not re-run inference.

## Report honestly

Say what was verified and how. "Matches the reference" means a measured difference on a shared
input, with the number and the region it is concentrated in — not "the code looks equivalent". Two
builds of the same weights (Core ML fp16 vs TFLite int8) never agree pixel for pixel, and saying so
is part of the result.
