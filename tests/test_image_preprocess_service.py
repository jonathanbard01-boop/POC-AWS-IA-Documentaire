from PIL import Image

from app.services.image_preprocess_service import analyze_image_quality


def test_non_image_returns_not_image(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("texte", encoding="utf-8")

    result = analyze_image_quality(path)

    assert result["is_image"] is False
    assert result["is_blank"] is None


def test_blank_image_is_detected(tmp_path):
    path = tmp_path / "blank.png"
    Image.new("RGB", (200, 200), "white").save(path)

    result = analyze_image_quality(path)

    assert result["is_image"] is True
    assert result["is_blank"] is True
    assert result["quality_score"] == 0.0


def test_non_blank_image_has_quality_metrics(tmp_path):
    path = tmp_path / "not_blank.png"
    image = Image.new("RGB", (200, 200), "white")
    for x in range(50, 150):
        for y in range(90, 110):
            image.putpixel((x, y), (0, 0, 0))
    image.save(path)

    result = analyze_image_quality(path)

    assert result["is_image"] is True
    assert result["is_blank"] is False
    assert result["blur_score"] is not None
    assert result["quality_score"] is not None
