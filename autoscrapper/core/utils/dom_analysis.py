import base64
import os
from typing import Dict
from PIL import Image
from core.utils.openai_client import get_ss_client, get_ss_model

class ImageAnalyzer:
    def __init__(self, image1_path: str, image2_path: str, next_step: str):
        self.image1_path = image1_path
        self.image2_path = image2_path
        self.next_step = next_step
        self.client = None

    def _encode_image_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _validate_images(self):
        for path in [self.image1_path, self.image2_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Image file not found: {path}")
            try:
                Image.open(path)
            except Exception as e:
                raise ValueError(f"Invalid image file {path}: {str(e)}")

    def analyze_images(self) -> Dict[str, str]:
        self._validate_images()
        self.client = get_ss_client()
        model = get_ss_model()

        base64_image1 = self._encode_image_to_base64(self.image1_path)
        base64_image2 = self._encode_image_to_base64(self.image2_path)

        prompt = f"""
        You are an excellent screenshot analysis agent. Analyze these two webpage screenshots in detail, considering that this was the action that was intended to be performed next: {self.next_step}.

        <rules>
        1. You have been provided 2 screenshots, one is the state of the webpage before the action was performed and the other is the state of the webpage after the action was performed.
        2. If the action was successfully performed, you should be able to see the expected changes in the webpage.
        3. We do not need generic description of what you see in the screenshots that has changed, we need the information and inference on whether the action was successfully performed or not.
        4. If the action was successfully performed, then you need to convey that information and along with that information, you also need to provide information on what changes you see in the screenshots that might have resulted from the action.
        5. If the action was not successfully performed, then you need to convey that information and along with that information, you also need to provide information on what changes you see in the screenshots that might have resulted from the action that indicate the tool call was not executed.

        <special_case>
        1. One special case is that when the action is searching, we are using SERP API so it will be that the webpage does not change at all. In that case, you need to provide information that the dom was unchanged. 
        2. So if the action is searching then you need to provide information that the dom was unchanged. The dom being unchanges in the case of search is a special case and does not conclude failure of the search action.
        </special_case>       
        </rules>
        """

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image1}",
                                    "detail": "high"
                                }
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image2}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")