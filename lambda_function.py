import boto3
import os
import urllib.parse
from PIL import Image, ImageOps

s3 = boto3.client("s3")

OUTPUT_BUCKET = "ram-image-resizer-output-2026"

SIZES = {
    "thumbnail": (150, 150),
    "medium": (800, 800),
    "large": (1600, 1600)
}

def lambda_handler(event, context):
    try:
        record = event["Records"][0]

        input_bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(
            record["s3"]["object"]["key"]
        )

        if not key.lower().endswith((".jpg", ".jpeg", ".png")):
            return {
                "statusCode": 200,
                "body": "Not an image file"
            }

        file_name = os.path.basename(key)
        input_path = f"/tmp/{file_name}"

        s3.download_file(input_bucket, key, input_path)

        with Image.open(input_path) as original_image:

            original_image = ImageOps.exif_transpose(original_image)

            for folder, size in SIZES.items():

                image = original_image.copy()
                image.thumbnail(size)

                output_path = f"/tmp/{folder}_{file_name}"

                if file_name.lower().endswith((".jpg", ".jpeg")):
                    if image.mode != "RGB":
                        image = image.convert("RGB")

                    image.save(
                        output_path,
                        format="JPEG",
                        quality=85,
                        optimize=True
                    )

                    content_type = "image/jpeg"

                else:
                    image.save(
                        output_path,
                        format="PNG",
                        optimize=True
                    )

                    content_type = "image/png"

                output_key = f"{folder}/{file_name}"

                s3.upload_file(
                    output_path,
                    OUTPUT_BUCKET,
                    output_key,
                    ExtraArgs={
                        "ContentType": content_type
                    }
                )

        return {
            "statusCode": 200,
            "body": "Images resized successfully"
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        raise
