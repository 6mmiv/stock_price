# -*- coding: utf-8 -*-
"""
네이버 + KRX 기반 주식 모니터링 GUI

변경 핵심
- 종목 검색: 네이버 검색 API 대신 KRX 상장법인 목록에서 회사명/코드 검색
  - KOSPI + KOSDAQ만 사용
  - '삼성전자', '005930' 둘 다 검색 가능
"""

import csv
import os
import time
import subprocess
import urllib.parse

from tkinter import (
    Tk, Frame, Label, Button, Entry, StringVar,
    Toplevel, messagebox, simpledialog
)
from tkinter import ttk

import pandas as pd
import requests

# buying_quantity 모듈은 있으면 사용, 없으면 옵션 기능 비활성화
try:
    import buying_quantity as bq
except ImportError:
    bq = None

# -----------------------------
# 기본 설정
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "stock.csv")

# 시세 관련 네이버 API
API_STOCK_DETAIL = "https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
API_KOSPI_INDEX = "https://polling.finance.naver.com/api/realtime/domestic/index/KOSPI"

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

UPDATE_INTERVAL_MS = 5000          # 포트폴리오 시세 갱신 간격 (5초)
AUTO_EXIT_AFTER_MS = 30 * 60 * 1000  # 30분 후 자동 종료

# KRX 마켓 코드 (KOSPI/KOSDAQ만 사용)
MARKET_CODE_DICT = {
    "KOSPI": "stockMkt",
    "KOSDAQ": "kosdaqMkt",
}


# -----------------------------
# 유틸 함수들
# -----------------------------

def format_int(value):
    """정수에 천 단위 콤마를 붙여 문자열로 반환."""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return ""


def fetch_stock_detail(code):
    """
    네이버 polling API에서 개별 종목 현재가/이름을 가져온다.
    :param code: 6자리 종목코드 문자열 (예: '005930')
    :return: (name:str, price:int)
    """
    url = API_STOCK_DETAIL.format(code=code)
    resp = requests.get(url, headers=REQUEST_HEADERS, timeout=3)
    resp.raise_for_status()
    data = resp.json()
    info = data["datas"][0]

    name = info["stockName"]
    price_str = info["closePrice"].replace(",", "")
    price = int(price_str)
    return name, price


def fetch_kospi_index():
    """KOSPI 지수 closePrice 문자열을 가져온다(그대로 출력용)."""
    resp = requests.get(API_KOSPI_INDEX, headers=REQUEST_HEADERS, timeout=3)
    resp.raise_for_status()
    data = resp.json()
    info = data["datas"][0]
    return info["closePrice"]


def download_krx_codes(markets=("KOSPI", "KOSDAQ")):
    """
    KRX 상장법인 목록에서 KOSPI/KOSDAQ 종목 리스트를 DataFrame으로 가져온다.
    - 회사명, 종목코드(6자리 문자열), 시장구분(KOSPI/KOSDAQ) 컬럼만 사용.
    참고: KIND 상장법인목록 엑셀은 실질적으로 HTML 테이블 형식이며,
          pandas.read_html 로 바로 읽을 수 있다.:contentReference[oaicite:1]{index=1}
    """
    frames = []

    for market in markets:
        url = "http://kind.krx.co.kr/corpgeneral/corpList.do"
        market_type = MARKET_CODE_DICT[market]
        params = {
            "method": "download",
            "searchType": 13,  # 상장법인만
            "marketType": market_type,
        }
        headers = {
            "User-Agent": "Mozilla/5.0",
        }
        r1 = requests.get(url, params=params, headers=headers)

        df = pd.read_html(r1.text)[0]

        # 종목코드는 숫자로 들어오므로 6자리 문자열로 변환
        # df["종목코드"] = df["종목코드"].map(lambda x: f"{int(x):06d}")
        df["시장구분"] = market
        frames.append(df[["회사명", "종목코드", "시장구분"]])

    if not frames:
        return pd.DataFrame(columns=["회사명", "종목코드", "시장구분"])

    return pd.concat(frames, ignore_index=True)


# -----------------------------
# 메인 앱
# -----------------------------

class StockApp(Tk):
    def __init__(self):
        super().__init__()

        self.title("Naver Stock Monitor")
        self.geometry("980x640")
        self.resizable(False, True)

        # 포트폴리오 데이터
        self.portfolio = []
        # 종목 검색 결과
        self.search_results = []

        # 화면에 바인딩할 StringVar
        self.kospi_var = StringVar()
        self.total_profit_var = StringVar()
        self.total_eval_var = StringVar()
        self.time_var = StringVar()
        self.search_keyword_var = StringVar()

        # KRX 상장법인 마스터 (KOSPI + KOSDAQ)
        self.krx_df = self.load_krx_master()

        # UI 구성
        self._build_ui()

        # 포트폴리오 CSV 로드
        self.load_portfolio()

        # 초기 표시
        self.refresh_table()
        self.update_totals()

        # 주기적 업데이트
        self.update_all()
        self.update_clock()

        # 30분 후 자동 종료
        self.after(AUTO_EXIT_AFTER_MS, self.on_auto_exit)

    # -------------------------
    # KRX 마스터 로드
    # -------------------------

    def load_krx_master(self):
        """KRX에서 KOSPI/KOSDAQ 상장 종목 전체 목록을 읽어온다."""
        try:
            df = download_krx_codes()
            return df
        except Exception as e:
            messagebox.showerror(
                "오류",
                "KRX 상장법인 목록을 불러오지 못했습니다.\n"
                "종목 검색(삼성전자 등)이 동작하지 않으면 이 부분을 먼저 확인해 주세요.\n\n"
                f"{e}"
            )
            return pd.DataFrame(columns=["회사명", "종목코드", "시장구분"])

    # -------------------------
    # UI 구성
    # -------------------------

    def _build_ui(self):
        label_font = ("맑은 고딕", 11, "bold")
        value_font = ("맑은 고딕", 11)

        # 상단 정보 영역
        top = Frame(self, bg="#E6E6FA", padx=10, pady=6)
        top.pack(side="top", fill="x")

        Label(top, text="KOSPI:", bg="#E6E6FA", font=label_font).pack(side="left")
        Label(top, textvariable=self.kospi_var,
              bg="#E6E6FA", font=value_font).pack(side="left", padx=(4, 20))

        Label(top, text="총 손익:", bg="#E6E6FA", font=label_font).pack(side="left")
        Label(top, textvariable=self.total_profit_var,
              bg="#E6E6FA", font=value_font).pack(side="left", padx=(4, 20))

        Label(top, text="총 평가금액:", bg="#E6E6FA", font=label_font).pack(side="left")
        Label(top, textvariable=self.total_eval_var,
              bg="#E6E6FA", font=value_font).pack(side="left", padx=(4, 20))

        Label(top, textvariable=self.time_var,
              bg="#E6E6FA", font=value_font).pack(side="right")

        # 중앙 포트폴리오 테이블
        center = Frame(self)
        center.pack(side="top", fill="both", expand=True, padx=10, pady=(4, 4))

        columns = (
            "name",
            "code",
            "current_price",
            "avg_price",
            "quantity",
            "profit_rate",
            "profit",
        )
        self.tree = ttk.Treeview(center, columns=columns, show="headings", height=15)

        self.tree.heading("name", text="종목명")
        self.tree.heading("code", text="코드")
        self.tree.heading("current_price", text="현재가")
        self.tree.heading("avg_price", text="평단가")
        self.tree.heading("quantity", text="수량")
        self.tree.heading("profit_rate", text="수익률(%)")
        self.tree.heading("profit", text="손익")

        self.tree.column("name", width=170, anchor="w")
        self.tree.column("code", width=80, anchor="center")
        self.tree.column("current_price", width=100, anchor="e")
        self.tree.column("avg_price", width=100, anchor="e")
        self.tree.column("quantity", width=70, anchor="e")
        self.tree.column("profit_rate", width=90, anchor="e")
        self.tree.column("profit", width=120, anchor="e")

        vsb = ttk.Scrollbar(center, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        center.columnconfigure(0, weight=1)
        center.rowconfigure(0, weight=1)

        # 하단: 검색/버튼 영역
        bottom = Frame(self)
        bottom.pack(side="bottom", fill="x", padx=10, pady=(0, 8))

        # 종목 검색 프레임
        search_frame = ttk.LabelFrame(bottom, text="종목 검색/추가")
        search_frame.pack(side="left", fill="both", expand=True)

        Entry(search_frame, textvariable=self.search_keyword_var, width=24).grid(
            row=0, column=0, padx=4, pady=4, sticky="w"
        )
        Button(
            search_frame,
            text="검색",
            command=self.on_search_clicked,
            width=8
        ).grid(row=0, column=1, padx=4, pady=4, sticky="w")

        # 검색 결과 테이블 (종목명 / 코드 / 현재가)
        s_columns = ("s_name", "s_code", "s_price")
        self.search_tree = ttk.Treeview(
            search_frame, columns=s_columns, show="headings", height=6
        )

        self.search_tree.heading("s_name", text="종목명")
        self.search_tree.heading("s_code", text="코드")
        self.search_tree.heading("s_price", text="현재가")

        self.search_tree.column("s_name", width=180, anchor="w")
        self.search_tree.column("s_code", width=80, anchor="center")
        self.search_tree.column("s_price", width=100, anchor="e")

        s_vsb = ttk.Scrollbar(
            search_frame, orient="vertical", command=self.search_tree.yview
        )
        self.search_tree.configure(yscrollcommand=s_vsb.set)

        self.search_tree.grid(
            row=1, column=0, columnspan=2,
            padx=4, pady=(0, 4), sticky="nsew"
        )
        s_vsb.grid(row=1, column=2, sticky="ns", pady=(0, 4))

        search_frame.columnconfigure(0, weight=1)
        search_frame.rowconfigure(1, weight=1)

        # 검색 결과 더블클릭 → 포트폴리오 추가
        self.search_tree.bind("<Double-1>", self.on_search_item_double_clicked)

        Button(
            search_frame,
            text="선택 종목 추가",
            command=self.on_add_selected_from_search,
            width=15,
        ).grid(row=2, column=0, padx=4, pady=(0, 4), sticky="w")

        Button(
            search_frame,
            text="선택 종목 삭제(포트폴리오)",
            command=self.on_delete_selected_portfolio,
            width=18,
        ).grid(row=2, column=1, padx=4, pady=(0, 4), sticky="e")

        # 오른쪽 보조 버튼
        side = Frame(bottom)
        side.pack(side="right", fill="y")

        Button(
            side,
            text="순매수 현황",
            command=self.show_pure_buying_window,
            width=14,
        ).pack(padx=4, pady=4)

        Button(
            side,
            text="CSV 열기",
            command=self.open_csv_external,
            width=14,
        ).pack(padx=4, pady=4)

        Button(
            side,
            text="종료",
            command=self.destroy,
            width=14,
        ).pack(padx=4, pady=4)

    # -------------------------
    # CSV 입출력
    # -------------------------

    def load_portfolio(self):
        """stock.csv에서 포트폴리오 읽기."""
        if not os.path.exists(CSV_PATH):
            return

        self.portfolio.clear()
        try:
            with open(CSV_PATH, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row.get("code")
                    name = row.get("name", "")
                    avg_price_str = row.get("price") or row.get("avg_price")
                    quantity_str = row.get("quantity")

                    if not code or not avg_price_str or not quantity_str:
                        continue

                    try:
                        avg_price = int(avg_price_str)
                        quantity = int(quantity_str)
                    except ValueError:
                        continue

                    self.portfolio.append(
                        {
                            "code": code,
                            "name": name,
                            "avg_price": avg_price,
                            "quantity": quantity,
                            "current_price": 0,
                            "profit": 0,
                            "profit_rate": 0.0,
                        }
                    )
        except Exception as e:
            messagebox.showerror(
                "오류",
                f"CSV 파일을 읽는 중 오류가 발생했습니다.\n{e}"
            )

    def save_portfolio(self):
        """포트폴리오를 stock.csv에 저장."""
        try:
            with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["code", "name", "price", "quantity"])
                for item in self.portfolio:
                    writer.writerow(
                        [
                            item["code"],
                            item.get("name", ""),
                            item["avg_price"],
                            item["quantity"],
                        ]
                    )
        except Exception as e:
            messagebox.showerror(
                "오류",
                f"CSV 파일을 저장하는 중 오류가 발생했습니다.\n{e}"
            )

    # -------------------------
    # 시세/손익 갱신
    # -------------------------

    def update_all(self):
        """KOSPI, 개별 종목 시세, 손익, 합계 갱신."""
        self.update_kospi()
        self.update_prices()
        self.update_totals()
        self.refresh_table()
        self.after(UPDATE_INTERVAL_MS, self.update_all)

    def update_kospi(self):
        try:
            value = fetch_kospi_index()
            self.kospi_var.set(value)
        except Exception:
            pass

    def update_prices(self):
        """포트폴리오 종목의 현재가 및 손익 계산."""
        for item in self.portfolio:
            code = item["code"]
            try:
                name, price = fetch_stock_detail(code)
                item["name"] = name
                item["current_price"] = price

                if item["avg_price"] > 0:
                    diff = price - item["avg_price"]
                    profit = diff * item["quantity"]
                    rate = diff * 100.0 / item["avg_price"]
                else:
                    profit = 0
                    rate = 0.0

                item["profit"] = profit
                item["profit_rate"] = rate
            except Exception:
                # 네트워크/파싱 오류 시 기존 값 유지
                continue

    def update_totals(self):
        """총 손익 및 총 평가금액 계산."""
        total_profit = 0
        total_eval = 0

        for item in self.portfolio:
            total_profit += int(item.get("profit", 0))
            current_price = item.get("current_price", 0)
            quantity = item.get("quantity", 0)
            total_eval += int(current_price) * int(quantity)

        self.total_profit_var.set(f"{format_int(total_profit)} 원")
        self.total_eval_var.set(f"{format_int(total_eval)} 원")

    def refresh_table(self):
        """포트폴리오 Treeview 갱신."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        for item in self.portfolio:
            name = item.get("name", "")
            code = item["code"]
            cur = format_int(item.get("current_price", 0))
            avg = format_int(item.get("avg_price", 0))
            qty = format_int(item.get("quantity", 0))
            profit = format_int(item.get("profit", 0))
            rate = item.get("profit_rate", 0.0)

            self.tree.insert(
                "",
                "end",
                values=(
                    name,
                    code,
                    cur,
                    avg,
                    qty,
                    f"{rate:.2f}",
                    profit,
                ),
            )

    # -------------------------
    # 시계 / 자동 종료
    # -------------------------

    def update_clock(self):
        now = time.strftime("%Y-%m-%d (%a) %H:%M:%S")
        self.time_var.set(now)
        self.after(1000, self.update_clock)

    def on_auto_exit(self):
        messagebox.showinfo("자동 종료", "30분이 경과하여 프로그램을 종료합니다.")
        self.destroy()

    # -------------------------
    # 검색/추가/삭제
    # -------------------------

    def find_stocks_in_krx(self, keyword, max_results=50):
        """
        KRX 상장법인 목록(self.krx_df)에서 회사명/코드로 검색.
        - KOSPI/KOSDAQ만 포함됨.
        - keyword가 숫자면 종목코드 기준, 아니면 회사명 기준 부분검색.
        반환: [{code, name, price}, ...]
        """
        kw = keyword.strip()
        if not kw or self.krx_df.empty:
            return []

        df = self.krx_df

        # 숫자면 코드 검색, 아니면 회사명 검색
        if kw.isdigit():
            code = kw.zfill(6)
            mask = df["종목코드"].str.contains(code)
        else:
            mask = df["회사명"].str.contains(kw, case=False, na=False)

        candidates = df[mask].sort_values(["회사명"]).head(max_results)

        results = []
        for _, row in candidates.iterrows():
            code = row["종목코드"]
            name = row["회사명"]
            price = None
            try:
                # 검색 결과에도 현재가를 보여주고 싶으면 사용
                _, price = fetch_stock_detail(code)
            except Exception:
                pass

            results.append(
                {
                    "code": code,
                    "name": name,
                    "price": price,
                }
            )
        return results

    def on_search_clicked(self):
        """검색 버튼 클릭 시: KRX 마스터에서 종목 검색."""
        keyword = self.search_keyword_var.get()
        if not keyword.strip():
            messagebox.showinfo("알림", "검색어를 입력하세요.")
            return

        try:
            self.search_results = self.find_stocks_in_krx(keyword)
        except Exception as e:
            messagebox.showerror("오류", f"종목 검색 중 오류가 발생했습니다.\n{e}")
            return

        # 검색 결과 표시 갱신
        for row in self.search_tree.get_children():
            self.search_tree.delete(row)

        for item in self.search_results:
            name = item["name"]
            code = item["code"]
            price = item["price"]
            price_str = format_int(price) if price is not None else ""
            self.search_tree.insert(
                "", "end", values=(name, code, price_str)
            )

    def _add_stock_to_portfolio(self, code, name):
        """평단가/수량 입력 받아 포트폴리오에 추가 또는 수정."""
        avg_price = simpledialog.askinteger(
            "평단가 입력",
            f"{name} ({code})의 평균 매수가(원)를 입력하세요.",
            minvalue=1,
        )
        if avg_price is None:
            return

        quantity = simpledialog.askinteger(
            "수량 입력",
            f"{name} ({code})의 보유 수량(주)을 입력하세요.",
            minvalue=1,
        )
        if quantity is None:
            return

        found = False
        for item in self.portfolio:
            if item["code"] == code:
                item["name"] = name
                item["avg_price"] = avg_price
                item["quantity"] = quantity
                found = True
                break

        if not found:
            self.portfolio.append(
                {
                    "code": code,
                    "name": name,
                    "avg_price": avg_price,
                    "quantity": quantity,
                    "current_price": 0,
                    "profit": 0,
                    "profit_rate": 0.0,
                }
            )

        self.save_portfolio()
        self.update_prices()
        self.update_totals()
        self.refresh_table()

    def on_search_item_double_clicked(self, event):
        """검색 결과 더블클릭 → 포트폴리오 추가."""
        sel = self.search_tree.selection()
        if not sel:
            return

        values = self.search_tree.item(sel[0], "values")
        if not values:
            return

        name, code, _ = values
        self._add_stock_to_portfolio(code, name)

    def on_add_selected_from_search(self):
        """검색 결과에서 선택한 한 종목을 포트폴리오에 추가."""
        sel = self.search_tree.selection()
        if not sel:
            messagebox.showinfo("알림", "검색 결과에서 추가할 종목을 선택하세요.")
            return

        values = self.search_tree.item(sel[0], "values")
        if not values:
            return

        name, code, _ = values
        self._add_stock_to_portfolio(code, name)

    def on_delete_selected_portfolio(self):
        """포트폴리오 테이블에서 선택한 종목 삭제."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("알림", "삭제할 종목을 포트폴리오에서 선택하세요.")
            return

        values = self.tree.item(sel[0], "values")
        if not values:
            return

        name, code = values[0], values[1]
        if messagebox.askyesno("삭제 확인", f"{name} ({code})를 삭제하시겠습니까?"):
            self.portfolio = [p for p in self.portfolio if p["code"] != code]
            self.save_portfolio()
            self.update_totals()
            self.refresh_table()

    # -------------------------
    # 순매수 현황 / CSV 열기
    # -------------------------

    def show_pure_buying_window(self):
        """buying_quantity 모듈이 있을 때만 순매수 현황 Toplevel 표시."""
        if bq is None:
            messagebox.showwarning(
                "모듈 없음",
                "buying_quantity 모듈을 찾을 수 없습니다.\n"
                "이 기능을 사용하려면 buying_quantity.py를 준비해 주세요.",
            )
            return

        try:
            text_kospi = bq.get_today_kospi_pure_buying_quantity()
            text_kosdaq = bq.get_today_kosdaq_pure_buying_quantity()
        except Exception as e:
            messagebox.showerror(
                "오류",
                f"순매수 현황을 가져오는 중 오류가 발생했습니다.\n{e}"
            )
            return

        win = Toplevel(self)
        win.title("순매수 현황")
        win.geometry("+1400+800")

        font = ("맑은 고딕", 11, "bold")

        Label(
            win,
            text="지수           날짜           기관        기타법인         개인       외국인",
            font=font,
            bg="#E6E6FA",
        ).grid(row=0, column=0, padx=4, pady=4, sticky="w")

        Label(
            win,
            text=str(text_kospi),
            font=font,
            bg="#E6E6FA",
        ).grid(row=1, column=0, padx=4, pady=2, sticky="w")

        Label(
            win,
            text=str(text_kosdaq),
            font=font,
            bg="#E6E6FA",
        ).grid(row=2, column=0, padx=4, pady=2, sticky="w")

    def open_csv_external(self):
        """stock.csv를 OS 기본 프로그램으로 연다."""
        if not os.path.exists(CSV_PATH):
            self.save_portfolio()

        try:
            if os.name == "nt":
                os.startfile(CSV_PATH)
            else:
                subprocess.run(["xdg-open", CSV_PATH], check=False)
        except Exception as e:
            messagebox.showerror(
                "오류",
                f"CSV 파일을 열 수 없습니다.\n{e}"
            )


# -----------------------------
# 진입점
# -----------------------------

if __name__ == "__main__":
    app = StockApp()
    app.mainloop()
