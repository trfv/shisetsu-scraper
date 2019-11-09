# coding: utf-8
import datetime

# from src.controller import koutou
from src.controller import edogawa

def main():
    # koutou.main(datetime.date.today() + datetime.timedelta(days=1))
    edogawa.main(datetime.date.today() + datetime.timedelta(days=1))

if __name__ == '__main__':
    main()