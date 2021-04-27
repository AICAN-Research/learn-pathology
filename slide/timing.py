import time


class Timer():
    def __init__(self, name):
        self.name = name
        self.start_time = time.time()
        self.sum = 0
        self.counter = 0
        self.max = 0
        self.min = 9999

    def start(self):
        self.start_time = time.time()

    def stop(self):
        runtime = (time.time() - self.start_time)*1000 # convert to ms
        self.max = max(self.max, runtime)
        self.min = min(self.max, runtime)
        self.sum += runtime
        self.counter += 1

    def print(self):
        print()
        print("Runtime of ", self.name)
        print("-------------------------------------")
        print("Average: " + str(self.sum/self.counter) + " ms")
        print("Max: " + str(self.max) + " Min: " + str(self.min))
        print("Count: " + str(self.counter))


