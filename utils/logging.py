# from colorama import Fore, Style

# def print_restaurant_header(service: str, category: str, model_name: str, ref: list, c_elapsed: float):
#     """Restaurant 원고 생성 시작 로그 출력"""
#     divider = f"{Fore.CYAN}{'═' * 70}{Style.RESET_ALL}"

#     info = [
#         (f"{Fore.GREEN}🚀 서비스명{Style.RESET_ALL}", service.upper()),
#         (f"{Fore.GREEN}📂 카테고리{Style.RESET_ALL}", category),
#         (f"{Fore.GREEN}🤖 사용모델{Style.RESET_ALL}", model_name),
#         (f"{Fore.GREEN}📝 참조원고{Style.RESET_ALL}", "✅ 있음" if ref else "❌ 없음"),
#         (f"{Fore.GREEN}⏱️  분류시간{Style.RESET_ALL}", f"{c_elapsed:.2f}초"),
#     ]

#     print("\n" + divider)
#     print(f"{Fore.MAGENTA}🍽️  RESTAURANT 원고 생성기".center(70) + Style.RESET_ALL)
#     print(divider)

#     for label, value in info:
#         print(f"{label:<15} : {value}")

#     print(divider)
#     print(f"{Fore.YELLOW}✨ 상태       : 원고 생성 준비 완료!{Style.RESET_ALL}")
#     print(divider + "\n")
