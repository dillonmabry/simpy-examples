"""
Basic M/M/1 Queue example via Simpy
Customer arrivals follow a poisson process
Service times follow exponential distribution

Covers:
    - Resources
    - Events
    - MonitoredResource
"""

import random
import statistics
import simpy

RANDOM_SEED = 42
ARRIVAL_INTERVAL = 10.0  # lambda
SERVICE_TIME = 8.0  # mu
SIM_TIME = 10000


class MonitoredResource(simpy.Resource):
    """MonitoredResource: custom class for monitoring
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = []
        self.total_service_time = 0.0
        self.customer_times = []
        self.wait_times = []

    def request(self, *args, **kwargs):
        self.data.append((self._env.now, len(self.queue)))
        return super().request(*args, **kwargs)

    def release(self, *args, **kwargs):
        self.data.append((self._env.now, len(self.queue)))
        return super().release(*args, **kwargs)


def arrival(env, interval, mu, resource):
    """Arrival process
    Args:
        env: Simpy environment
        interval: interval of arrival (every x minutes)
        mu: service time of resource
        resource: Resource to use
    """
    i = 0
    while True:
        customer = serve(env, "Customer%02d" % i, resource, mu)
        env.process(customer)
        arrival_time = random.expovariate(1.0 / interval)
        yield env.timeout(arrival_time)
        i += 1


def serve(env, name, resource, mu):
    """Customer arrives, is served, and leaves
    Args:
        env: Simpy environment
        name: name of customer
        resource: Resource to use
        mu: service time of server
    """
    arrive = env.now
    print("%s arrives at %.2f" % (name, arrive))

    with resource.request() as req:
        yield req
        wait = env.now - arrive
        resource.wait_times.append(wait)
        # Got resource
        print("%s to resource, waited %.2f" % (name, wait))
        service_time = random.expovariate(1.0 / mu)
        resource.total_service_time += service_time
        yield env.timeout(service_time)
        resource.customer_times.append((env.now - arrive))
        print('%s finished %.2f' % (name, env.now))


if __name__ == "__main__":
    random.seed(RANDOM_SEED)
    env = simpy.Environment()

    res = MonitoredResource(env, capacity=1)
    env.process(arrival(env, ARRIVAL_INTERVAL, SERVICE_TIME, res))
    env.run(until=SIM_TIME)

    print("\n")
    AVG_WAIT = statistics.mean(res.wait_times)
    print("Average wait time: %.2f" % (AVG_WAIT))
    AVG_CUSTOMERS = sum(res.customer_times) / SIM_TIME
    print("Average number of customers in system: %.2f" % (AVG_CUSTOMERS))
    AVG_UTIL = res.total_service_time / SIM_TIME
    print("Average utilization: %.2f" % (AVG_UTIL))
    print("\n")
    mu = (1 / SERVICE_TIME)
    la = (1 / ARRIVAL_INTERVAL)
    T_WAIT_TIME = 1 / (mu - la)
    print("Theoretical wait time: %.2f" % (T_WAIT_TIME))
    T_AVG_CUSTOMERS = (la**2) / ((mu * mu) - (mu * la))
    print("Theoretical number of customers in system: %.2f" % (T_AVG_CUSTOMERS))
    T_AVG_UTIL = la / mu
    print("Theoretical utilization: %.2f" % (T_AVG_UTIL))
