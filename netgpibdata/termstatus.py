
import sys


class statusTxt:
    def __init__(self, initTxt):
        self.txtlen = len(initTxt)
        self.txt = initTxt
        print(initTxt, end=' ')
        sys.stdout.flush()

    def update(self, updateTxt):
        print("\010" + "\010" * self.txtlen + updateTxt, end=' ')
        sys.stdout.flush()
        self.txtlen = len(updateTxt)
        self.txt = updateTxt

    def end(self, updateTxt=""):
        if updateTxt == "":
            print("")
        else:
            print("\010" + "\010" * self.txtlen + updateTxt)

        sys.stdout.flush()


class progressBar:
    def __init__(self, width, nTot):
        self.width = width
        self.nTot = nTot
        self.stepped = 0
        print('[' + ' ' * width + ']', end=' ')
        print('\b' * (width + 2), end=' ')
        sys.stdout.flush()
        self.done = False

    def update(self, val):
        steps = int(round(val / self.nTot * self.width))
        if steps > self.stepped:
            for ii in range(steps - self.stepped):
                print('\b' + '*', end=' ')
            sys.stdout.flush()
            self.stepped = steps

        if val == self.nTot:
            self.end()

    def end(self):
        if self.done is False:
            print('\b] Done!')
            sys.stdout.flush()
            self.done = True
