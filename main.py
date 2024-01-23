# this is an alternative entry point to using scripts/run.sh, intended for debugging in Pycharm
import app

if __name__ == "__main__":
    app.create_app().run(debug=True)
