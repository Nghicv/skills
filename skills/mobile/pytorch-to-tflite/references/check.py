"""Runs a .tflite on a real image, reports the tensors, and renders the output to look at.

    check.py model.tflite photo.jpg out.png [--preprocess imagenet|unit|raw] [--labels labels.txt]

Reads the input size and layout from the interpreter rather than assuming them, and renders by
output shape: a single-channel map as a normalised image, three channels as RGB, per-class scores
as an argmax palette (plus the top-5 printed).

Use a real photograph. A synthetic gradient hides preprocessing mistakes; if the wrong
normalisation is applied, the output still has the right shape and means nothing, and only a real
scene makes that obvious.
"""

import argparse

import numpy as np
from ai_edge_litert.interpreter import Interpreter
from PIL import Image

IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def layout_of(shape):
    """Returns (height, width, channels_first) for a 4D image input."""
    shape = list(shape)
    if len(shape) != 4:
        raise SystemExit(f"expected a 4D image input, got {shape}")
    if shape[3] in (1, 3, 4):
        return shape[1], shape[2], False
    if shape[1] in (1, 3, 4):
        return shape[2], shape[3], True
    raise SystemExit(f"cannot tell which axis is channels: {shape}")


def preprocess(path, height, width, channels_first, mode, dtype):
    image = Image.open(path).convert("RGB").resize((width, height), Image.BILINEAR)
    pixels = np.asarray(image, dtype=np.float32)
    if mode != "raw":
        pixels /= 255.0
    if mode == "imagenet":
        pixels = (pixels - IMAGENET_MEAN) / IMAGENET_STD
    if channels_first:
        pixels = pixels.transpose(2, 0, 1)
    return pixels[None].astype(dtype)


def render(output, out_path, labels):
    array = np.asarray(output).squeeze()
    print("output", array.shape, "min", round(float(array.min()), 4), "max", round(float(array.max()), 4))

    if array.ndim == 1:  # class scores
        top = np.argsort(array)[::-1][:5]
        for index in top:
            name = labels[index] if labels and index < len(labels) else str(index)
            print(f"  {name}: {array[index]:.4f}")
        return

    if array.ndim == 3 and array.shape[-1] == 3:  # an image
        image = array
        if image.max() <= 1.5:
            image = image * 255.0
        Image.fromarray(np.clip(image, 0, 255).astype(np.uint8)).save(out_path)
    elif array.ndim == 3 and array.shape[0] == 3:  # an image, channels first
        image = array.transpose(1, 2, 0)
        if image.max() <= 1.5:
            image = image * 255.0
        Image.fromarray(np.clip(image, 0, 255).astype(np.uint8)).save(out_path)
    elif array.ndim == 3:  # per-class scores per pixel
        classes = array.argmax(axis=0 if array.shape[0] < array.shape[-1] else -1)
        palette = ((classes * 47) % 256).astype(np.uint8)
        Image.fromarray(palette).save(out_path)
        print("  classes present:", sorted(set(classes.flatten().tolist()))[:12])
    else:  # a single-channel map, normalised so it can be seen
        span = float(array.max() - array.min()) or 1.0
        normalised = (array - array.min()) / span
        Image.fromarray((normalised * 255).astype(np.uint8)).save(out_path)
    print("wrote", out_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model")
    parser.add_argument("image")
    parser.add_argument("out")
    parser.add_argument(
        "--preprocess",
        default="imagenet",
        choices=("imagenet", "unit", "raw"),
        help="imagenet: /255 then mean/std; unit: /255; raw: 0..255. Which one is right is a "
        "property of the converted file — try both and look at the result.",
    )
    parser.add_argument("--labels", help="one class name per line, for class outputs")
    args = parser.parse_args()

    interpreter = Interpreter(model_path=args.model)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()[0]
    output_details = interpreter.get_output_details()[0]
    print(
        "input", input_details["shape"], input_details["dtype"].__name__,
        "| outputs", len(interpreter.get_output_details()),
        "first", output_details["shape"], output_details["dtype"].__name__,
    )

    height, width, channels_first = layout_of(input_details["shape"])
    tensor = preprocess(
        args.image, height, width, channels_first, args.preprocess, input_details["dtype"]
    )
    interpreter.set_tensor(input_details["index"], tensor)
    interpreter.invoke()

    labels = None
    if args.labels:
        labels = [line.strip() for line in open(args.labels, encoding="utf-8")]
    render(interpreter.get_tensor(output_details["index"]), args.out, labels)


if __name__ == "__main__":
    main()
