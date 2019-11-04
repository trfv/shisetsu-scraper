# coding: utf-8
import datetime

from src.controller import koutou

def main():
    koutou.main(datetime.date.today() + datetime.timedelta(days=1))

if __name__ == '__main__':
    main()