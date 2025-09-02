import anthropic

from config import CLAUDE_API_KEY


APP_KEY = CLAUDE_API_KEY

print(APP_KEY)


def file_upload(file_name):
    client = anthropic.Anthropic(api_key=APP_KEY)
    client.beta.files.upload(
        file=(
            f"{file_name}.txt",
            open(
                f"/Users/ganggyunggyu/Programing/21lab/blog_analyzer/_docs/claude_docs/{file_name}.txt",
                "rb",
            ),
            "text/plain",
        ),
    )


def get_file_list():
    import anthropic

    client = anthropic.Anthropic(api_key=APP_KEY)
    files = client.beta.files.list()
    print(files)
    return files


def get_file_ids():
    import anthropic

    client = anthropic.Anthropic(api_key=APP_KEY)
    all_ids = []
    starting_after = None

    while True:
        response = client.beta.files.list(
            limit=100,
        )
        files = response.data

        if not files:
            break

        all_ids.extend([f.id for f in files])
        starting_after = files[-1].id  # 다음 페이지로 이동

        if not response.has_more:  # 더 이상 없으면 중단
            break

    return all_ids


# for i in range(1, 61):
#     try:
#         file_upload(str(i))
#         print(f"{i}.txt 업로드 완료")
#     except Exception as e:
#         print(f"{i}.txt 업로드 실패: {e}")

# print(len(get_file_ids()))
