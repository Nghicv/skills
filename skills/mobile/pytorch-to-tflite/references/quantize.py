"""Quantises a .tflite to shrink the download.

    quantize.py model.tflite model_int8.tflite [--recipe weight_only_wi8_afp32]

`weight_only_wi8_afp32` is the safe default: weights become int8, activations stay fp32, and so do
the model's inputs and outputs — the Android side does not change at all. `dynamic_wi8_afp32`
quantises activations dynamically too, which is faster but moves the numbers more.

There is no float16 recipe in ai-edge-quantizer. Always re-run check.py on the quantised file and
compare against the fp32 output on the same input; report the difference rather than assuming it is
negligible.
"""

import argparse

from ai_edge_quantizer import quantizer, recipe


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("target")
    parser.add_argument(
        "--recipe",
        default="weight_only_wi8_afp32",
        help="any factory on ai_edge_quantizer.recipe, e.g. weight_only_wi8_afp32, "
        "dynamic_wi8_afp32, weight_only_wi4_afp32",
    )
    args = parser.parse_args()

    quantiser = quantizer.Quantizer(args.source)
    quantiser.load_quantization_recipe(getattr(recipe, args.recipe)())
    quantiser.quantize().export_model(args.target)
    print("wrote", args.target)


if __name__ == "__main__":
    main()
