# coding: utf-8
import datetime

# from src.koutou.controller import main as koutou
from src.edogawa.controller import main as edogawa

def main():
    # koutou.main(datetime.date.today() + datetime.timedelta(days=1))
    edogawa.main(datetime.date.today() + datetime.timedelta(days=1))

if __name__ == '__main__':
    main()