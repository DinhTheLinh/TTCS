import os
import json
import torch
import clip
from PIL import Image


class SketchRetrievalModel:
    def __init__(
        self,
        model_path="clip_triplet.pth",
        embeddings_path="photo_embeddings.pt",
        paths_json_path="photo_paths.json",
        device=None
    ):
        self.device = device if device is not None else (
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        # Load model
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
        self.model = self.model.float()
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

        # Load embeddings
        self.photo_features = torch.load(embeddings_path, map_location="cpu").float()
        self.photo_features = self.photo_features / self.photo_features.norm(
            dim=-1, keepdim=True
        ).clamp(min=1e-8)

        # Load paths
        with open(paths_json_path, "r", encoding="utf-8") as f:
            self.photo_paths = json.load(f)

        if len(self.photo_paths) != self.photo_features.shape[0]:
            raise ValueError(
                f"Số lượng photo_paths ({len(self.photo_paths)}) "
                f"không khớp với số lượng embeddings ({self.photo_features.shape[0]})!"
            )

    def encode_sketch(self, sketch_path):
        if not os.path.exists(sketch_path):
            raise FileNotFoundError(f"Không tìm thấy sketch: {sketch_path}")

        image = Image.open(sketch_path).convert("RGBA")

        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[3])

        image = background

        image = self.preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            feat = self.model.encode_image(image)
            feat = feat / feat.norm(dim=-1, keepdim=True).clamp(min=1e-8)

        return feat.cpu()

    def get_class_name_from_path(self, image_path):
        """
        Lấy tên class từ thư mục cha của ảnh.
        Ví dụ:
            gallery/dog/abc.jpg -> dog
            data/photo/cat/xyz.jpg -> cat
        """
        return os.path.basename(os.path.dirname(image_path))
    def to_web_path(self, image_path):
        web_path = image_path.replace("\\", "/")
        idx = web_path.find("data/photo/")
        web_path = web_path[idx:]
        relative = web_path.replace("data/photo/", "")
        return f"http://localhost:8000/static/{relative}"
    def debug_check_class_names(self, num_samples=5):
        """
        In thử vài path đầu để kiểm tra class_name có lấy đúng không.
        """
        print(f"\n--- CHECK {num_samples} PHOTO PATHS ĐẦU ---")
        num_samples = min(num_samples, len(self.photo_paths))

        for i in range(num_samples):
            path = self.photo_paths[i]
            class_name = self.get_class_name_from_path(path)
            print(f"[{i}] PATH       : {path}")
            print(f"    DIRNAME    : {os.path.dirname(path)}")
            print(f"    CLASS_NAME : {class_name}")
            print("-" * 50)

    def predict(self, sketch_path, top_k=5):
        sketch_feat = self.encode_sketch(sketch_path)
        sims = (sketch_feat @ self.photo_features.T).squeeze(0)

        top_k = min(top_k, len(self.photo_paths))
        topk = torch.topk(sims, k=top_k)

        results = []
        top_indices = topk.indices.tolist()
        top_scores = topk.values.tolist()

        for rank, (idx, score) in enumerate(zip(top_indices, top_scores), start=1):
            image_path = self.photo_paths[idx]
            class_name = self.get_class_name_from_path(image_path)

            results.append({
                "rank": rank,
                "image_path": image_path,
                "image_url": self.to_web_path(image_path),  # 🔥 QUAN TRỌNG
                "score": float(score),
                "class_name": class_name
            })

        predicted_class = results[0]["class_name"] if results else None

        return {
            "sketch_path": sketch_path,
            "predicted_class": predicted_class,
            "results": results
        }


if __name__ == "__main__":
    model = SketchRetrievalModel(
        model_path="clip_triplet.pth",
        embeddings_path="photo_embeddings.pt",
        paths_json_path="photo_paths.json"
    )

    # 1. Check class_name có lấy đúng không
    model.debug_check_class_names(num_samples=5)

    # 2. Test predict
    test_sketch = r"D:\PROJECT\BTL TTCS\data (3)\data\sketch\dog\n02103406_343-3.png"   # đổi lại path sketch thật của bạn

    if os.path.exists(test_sketch):
        output = model.predict(test_sketch, top_k=5)

        print("\n=== KẾT QUẢ PREDICT ===")
        print("Sketch:", output["sketch_path"])
        print("Predicted class:", output["predicted_class"])
        print()

        for item in output["results"]:
            print(
                f"Top {item['rank']}: "
                f"class={item['class_name']} | "
                f"score={item['score']:.4f} | "
                f"path={item['image_path']}"
            )
    else:
        print(f"\nChưa tìm thấy file test sketch: {test_sketch}")
        print("Bạn hãy sửa biến test_sketch thành đường dẫn ảnh sketch thật để test.")