"""Traces a PyTorch model at a fixed input shape and exports TFLite.

    # segmentation head, NCHW input, output object with a named field
    convert.py --model nvidia/segformer-b0-finetuned-ade-512-512 \
               --auto-class AutoModelForSemanticSegmentation \
               --shape 1,3,512,512 --output-field logits --out model.tflite

    # classifier, NHWC-friendly size, first element of a tuple output
    convert.py --model google/mobilenet_v2_1.0_224 --auto-class AutoModelForImageClassification \
               --shape 1,3,224,224 --output-field logits --out model.tflite

    # a local checkpoint that already returns a tensor
    convert.py --checkpoint ./weights.pt --shape 1,3,256,256 --out model.tflite

The wrapper is the part that matters and the part to adapt: the converter wants plain tensors in
and out, while HF models return output objects and many models return several heads. Preprocessing
stays OUTSIDE the graph, so the caller applies it — check what the published file is expected to
receive, and keep that choice remote-config driven in the app.
"""

import argparse

import torch


class SingleTensor(torch.nn.Module):
    """One tensor in, one tensor out. Picks a field or index out of whatever the model returns."""

    def __init__(self, model, output_field=None, output_index=None):
        super().__init__()
        self.model = model
        self.output_field = output_field
        self.output_index = output_index

    def forward(self, pixel_values):
        out = self.model(pixel_values)
        if self.output_field:
            return getattr(out, self.output_field)
        if self.output_index is not None:
            return out[self.output_index]
        if isinstance(out, (tuple, list)):
            return out[0]
        return out


def load(args):
    if args.checkpoint:
        model = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
        return model.eval() if hasattr(model, "eval") else model
    import transformers

    return getattr(transformers, args.auto_class).from_pretrained(args.model).eval()


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--model", help="HuggingFace model id")
    source.add_argument("--checkpoint", help="path to a torch.save'd module")
    parser.add_argument("--auto-class", default="AutoModel", help="transformers Auto* class")
    parser.add_argument("--shape", required=True, help="input shape, e.g. 1,3,518,518")
    parser.add_argument("--output-field", help="attribute to take from the model's output")
    parser.add_argument("--output-index", type=int, help="index to take from a tuple output")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    # Imported late: it pulls in TensorFlow and is slow.
    import litert_torch

    shape = tuple(int(part) for part in args.shape.split(","))
    wrapper = SingleTensor(load(args), args.output_field, args.output_index).eval()
    sample = (torch.rand(*shape),)

    with torch.no_grad():
        reference = wrapper(*sample)
    print("torch output:", tuple(reference.shape), float(reference.min()), float(reference.max()))

    litert_torch.convert(wrapper, sample).export(args.out)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
