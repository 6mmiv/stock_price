from tkinter import Label, Tk, PhotoImage, Button, Toplevel
import time
from urllib.request import urlopen
from bs4 import BeautifulSoup
import locale
from pandas import read_csv
from subprocess32 import run
import buying_quantity as bq

def open_stock_price() :
    global time_lag
    global bomber_man
    time_lag = 0
    bomber_man = 0

    def get_stock_prices():
        stocks = read_csv("stock.csv", sep=' / ', engine='python')
        stock_nums = list((stocks['code']))
        for i in range(len(stock_nums)):
            if stock_nums[i] < 9999:
                stock_nums[i] = '00' + str(stock_nums[i])
            elif stock_nums[i] < 99999:
                stock_nums[i] = '0' + str(stock_nums[i])
        my_price = list(stocks['price'])
        my_volume = list(stocks['quantity'])

        def stock_code_update():
            stocks = read_csv("stock.csv", sep=' / ')
            stock_nums = list(stocks['code'])
            for i in range(len(stock_nums)):
                if stock_nums[i] < 9999:
                    stock_nums[i] = '00' + str(stock_nums[i])
                elif stock_nums[i] < 99999:
                    stock_nums[i] = '0' + str(stock_nums[i])
            my_price = list(stocks['price'])
            my_volume = list(stocks['quantity'])
            name()
            make_df()
            digital_clock()
            get_now_price()
            get_my_price()
            get_income_rate()
            get_income()
            get_kospi()

        now_price = [0] * len(stock_nums);
        income_rate = [0] * len(stock_nums);
        income = [0] * len(stock_nums)
        locale.setlocale(locale.LC_ALL, '')

        def get_name(stock_code):
            stock_url = urlopen('https://polling.finance.naver.com/api/realtime/domestic/stock/{}'.format(stock_code))
            stock_html = BeautifulSoup(stock_url, 'html.parser')
            stock_html_text = stock_html.get_text()
            name1 = stock_html_text.find('stockName\":')
            name2 = stock_html_text.find('\"', name1)
            name3 = stock_html_text.find('\"', name2 + 3)
            stock_name = stock_html_text[name2 + 3:name3]
            return stock_name

        def get_price(stock_code):
            stock_url = urlopen('https://polling.finance.naver.com/api/realtime/domestic/stock/{}'.format(stock_code))
            stock_html = BeautifulSoup(stock_url, 'html.parser')
            stock_html_text = stock_html.get_text()
            idx1 = stock_html_text.find('closePrice\":\"')
            idx2 = stock_html_text.find('\"', idx1)
            idx3 = stock_html_text.find('\"', idx2 + 3)
            stock_price = stock_html_text[idx2 + 3:idx3]
            return stock_price

        def get_kospi():
            stock_url = urlopen('https://polling.finance.naver.com/api/realtime/domestic/index/KOSPI')
            stock_html = BeautifulSoup(stock_url, 'html.parser')
            stock_html_text = stock_html.get_text()
            idx1 = stock_html_text.find('closePrice\":\"')
            idx2 = stock_html_text.find('\"', idx1)
            idx3 = stock_html_text.find('\"', idx2 + 3)
            stock_price = stock_html_text[idx2 + 3:idx3]
            kospi_label.config(text=str(stock_price))
            global time_lag
            if time_lag >= 1800:  # 1800초(30분)가 지나면 자동으로 다시 시작함
                app_window.destroy()
            time_lag += 1
            kospi_label.after(1000, get_kospi)

        def get_num(num):
            miv = ''
            aiw = []
            aiw = num.split(sep=',')
            for i in aiw:
                miv += i
            return int(miv)

        def name():
            miv = ''
            for i in stock_nums:
                miv = miv + '\n' + get_name(i)
            name_label.config(text=miv[1:])

        def make_df():
            miv = 0
            aiw = 0
            for i in range(len(stock_nums)):
                miv = get_num(get_price(stock_nums[i]))
                aiw = my_price[i]
                now_price[i] = miv
                if aiw == 0:
                    income[i] = 0
                    income_rate[i] = 0
                else:
                    i_income_rate = round((miv - aiw) * 100 / aiw, 2)
                    i_income = (miv - aiw) * my_volume[i]
                    income_rate[i] = i_income_rate
                    income[i] = int(i_income)
            miv = sum(income)
            sum_of_income.config(text=str(miv))
            sum_of_income.after(1000, make_df)

        def digital_clock():
            time_live = time.strftime("%y년-%#m월-%#d일-%a %H:%M:%S")
            time_label.config(text=time_live)
            time_label.after(200, digital_clock)

        def get_now_price():
            miv = ''
            for i in range(len(stock_nums)):
                miv = miv + '\n' + str(now_price[i])
            price_label.config(text=miv[1:])
            price_label.after(1000, get_now_price)

        def get_my_price():
            miv = ''
            for i in range(len(stock_nums)):
                miv = miv + '\n' + str(my_price[i])
            buy_price_label.config(text=miv[1:])

        def get_income_rate():
            miv = ''
            for i in range(len(stock_nums)):
                miv = miv + '\n' + str(income_rate[i]) + '%'
            income_rate_label.config(text=miv[1:])
            income_rate_label.after(1000, get_income_rate)

        def get_income():
            miv = ''
            for i in range(len(stock_nums)):
                miv = miv + '\n' + str(income[i])
            income_label.config(text=miv[1:])
            income_label.after(1000, get_income)

        def csvopen():
            run('notepad C:/Users/user/Documents/python/data_science/dist/stock_price/stock.csv')

        def boom():
            global bomber_man
            bomber_man += 1
            app_window.destroy()

        def pure_buying_quantity() :
            quantity1 = bq.get_today_kospi_pure_buying_quantity()
            quantity2 = bq.get_today_kosdaq_pure_buying_quantity()

            pbq = Toplevel(app_window)
            pbq.geometry('+1390+800')

            pbq_backgroud = PhotoImage(file="background.png")
            pbq_backgroud_label = Label(pbq, image=background)
            pbq_backgroud_label.place(x=-5, y=-5)

            pbq_label0 = Label(pbq, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39', bd=10,
                               text = '  지수           날짜           기관        기타법인         개인       외국인')
            pbq_label0.grid(row = 0, column = 0)

            pbq_label1 = Label(pbq, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39', bd=10,
                               text = quantity1)
            pbq_label1.grid(row = 1, column = 0)

            pbq_label2 = Label(pbq, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39', bd=10,
                               text=quantity2)
            pbq_label2.grid(row = 2, column = 0)



        app_window = Tk()
        app_window.title('Stock Price')
        app_window.geometry("520x{}+1390+{}".format(90 + 30 * len(stock_nums), 910 - 25 * len(stock_nums)))
        app_window.resizable(0, 1)

        label_font1 = '교보 손글씨 2020 박도연'
        label_font_size1 = 12

        background = PhotoImage(file="background.png")
        background_label = Label(app_window, image=background)
        background_label.place(x=-5, y=-5)

        kospi_label = Label(app_window, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39', bd=10)
        kospi_label.grid(row=0, column=0)

        sum_of_income = Label(app_window, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39',
                              bd=10)
        sum_of_income.grid(row=2, column=4)

        label1 = Label(app_window, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39', bd=10)
        label1.grid(row=0, column=1)
        label1.config(text='현재가')

        label2 = Label(app_window, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39', bd=10)
        label2.grid(row=0, column=2)
        label2.config(text='구매가')

        label3 = Label(app_window, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39', bd=10)
        label3.grid(row=0, column=3)
        label3.config(text='수익률')

        label4 = Label(app_window, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39', bd=10)
        label4.grid(row=0, column=4)
        label4.config(text='수익금')

        name_label = Label(app_window, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39', bd=10)
        name_label.grid(row=1, column=0)

        price_label = Label(app_window, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39', bd=10)
        price_label.grid(row=1, column=1)

        buy_price_label = Label(app_window, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39',
                                bd=10)
        buy_price_label.grid(row=1, column=2)

        income_rate_label = Label(app_window, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39',
                                  bd=10)
        income_rate_label.grid(row=1, column=3)

        income_label = Label(app_window, font=(label_font1, label_font_size1, 'bold'), bg='#E6E6Fa', fg='#4F4B39',
                             bd=10)
        income_label.grid(row=1, column=4)

        time_label = Label(app_window, font=(label_font1, 12, 'bold'), bg='#E6E6Fa', fg='#4F4B39', bd=10)
        time_label.grid(row=2, column=0)

        button1 = Button(app_window, text='종목추가', command=csvopen, width=7, font=(label_font1, label_font_size1),
                         bg='white')
        button1.grid(row=2, column=3)

        button2 = Button(app_window, text='boom', command=boom, width=7, font=(label_font1, label_font_size1),
                         bg='white')
        button2.grid(row=2, column=2)
        button3 = Button(app_window, text='순매수 현황', command = pure_buying_quantity, width = 7, font = (label_font1, label_font_size1),
                         bg = 'white')
        button3.grid(row = 2, column = 1)

        def open_window():
            name()
            make_df()
            digital_clock()
            get_now_price()
            get_my_price()
            get_income_rate()
            get_income()
            get_kospi()
            app_window.mainloop()

        open_window()

    while True:
        get_stock_prices()
        if bomber_man >= 1:
            break
        time_lag = 0

open_stock_price()