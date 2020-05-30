## Caution
- このディレクトリをそのまま1つのパッケージとしてデプロイする
- 区ごとに分割することで依存性を減らすことが狙い（将来的にはレポジトリを分割する可能性あり）
- ローカル環境で検証するときは、shisetsu-scraper/src/kita以下で実行すること。
```
shisetu-scraper/src/kita $ poetry run python main.py
```


（以下公式サイトのコピペ）

## Poetry
#### Install Poetry
- See [here](https://pypi.org/project/poetry/)
- Poetry provides a custom installer that will install poetry isolated from the rest of your system by vendorizing its dependencies.
- This is the recommended way of installing poetry.
```
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
```

- Alternatively, you can download the get-poetry.py file and execute it separately.
- If you want to install prerelease versions, you can do so by passing --preview to get-poetry.py:
```
python get-poetry.py --preview
```

- Similarly, if you want to install a specific version, you can use --version:
```
python get-poetry.py --version 0.7.0
```

- Using pip to install poetry is also possible.
```
pip install --user poetry
```
- Be aware, however, that it will also install poetry's dependencies which might cause conflicts.

## Heroku
#### Install the Heroku CLI
- Download and install the [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli).
- If you haven't already, log in to your Heroku account and follow the prompts to create a new SSH public key.
```
heroku login
```

#### Clone the repository
- Use Git to clone kita's source code to your local machine.
```
heroku git:clone -a kita
cd kita
```

#### Deploy your changes
- Make some changes to the code you just cloned and deploy them to Heroku using Git.
```
git add .
git commit -am "make it better"
git push heroku master
```
