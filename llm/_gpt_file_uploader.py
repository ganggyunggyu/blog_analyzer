from openai import OpenAI
from config import OPENAI_API_KEY


client = OpenAI(api_key=OPENAI_API_KEY)


def file_upload(file_name):
    try:
        with open(
            f"/Users/ganggyunggyu/Programing/21lab/text-gen-hub/_docs/merge_docs/{file_name}.txt",
            "rb",
        ) as f:
            response = client.files.create(
                file=f, purpose="assistants"  # or "fine-tune" if applicable
            )
            print(f"{file_name}.txt 업로드 완료: {response.id}")
            return response
    except Exception as e:
        print(f"{file_name}.txt 업로드 실패: {e}")


def get_file_list():
    try:
        response = client.files.list()
        print(response)
        return response
    except Exception as e:
        print(f"파일 목록 불러오기 실패: {e}")
        return []


def get_file_ids():
    try:
        files = get_file_list()
        return [f["id"] for f in files["data"]]
    except Exception as e:
        print(f"파일 ID 추출 실패: {e}")
        return []


def get_file_content():
    content = client.files.content("file-9zqSpcEWCiGL8sF5td2V73")
    print(content)
    return content
