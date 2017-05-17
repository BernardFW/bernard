from sanic import Sanic
from sanic.response import text

app = Sanic(__name__)


def main():
    @app.route("/")
    async def test(request):
        return text(app.config.GREETING)

    app.run(host="0.0.0.0", port=8000, debug=True)


if __name__ == '__main__':
    main()
