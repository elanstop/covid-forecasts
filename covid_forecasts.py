import datetime
import math
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
from matplotlib.ticker import ScalarFormatter

register_matplotlib_converters()


# NOTE: currently dropping days where the new deaths dropped because they reflect noise during this phase

class DeathForecast:

    def __init__(self, country, lag=17, reference=12, double_time = 2.7):
        self.doubling_time = 2.7
        self.deaths = pd.read_csv('deaths_data.csv')
        self.cases = pd.read_csv('cases.csv')
        self.country = country
        self.lag = lag
        self.reference = reference
        self.time_series = self.get_country().values.tolist()[0][4:]
        self.start = self.find_start()
        self.raw_dates = self.get_country().columns.values.tolist()
        self.recorded_deaths = self.get_new_daily_deaths()
        self.fitted_dates, self.fitted_cases, self.fit_doubling_time = self.fit_last_period()

    @staticmethod
    def convert_date(date):
        return datetime.datetime.strptime(date, "%m/%d/%y").date()

    def pad_dates(self):
        raw_last_date = self.raw_dates[-1]
        last_date = self.convert_date(raw_last_date)
        date_list = [last_date + datetime.timedelta(days=x) for x in range(self.lag)]
        return date_list

    def get_country(self, data_type='deaths'):
        if data_type == 'deaths':
            condition = self.deaths['Country/Region'] == self.country
            return self.deaths[condition]
        if data_type == 'cases':
            condition = self.cases['Country/Region'] == self.country
            return self.cases[condition]

    def find_start(self):
        data = self.time_series
        i = 0
        while data[i] < self.reference:
            i += 1
        return i

    def get_new_daily_deaths(self):
        data = self.time_series
        new_daily_deaths = []
        for i in range(self.start, len(data)):
            raw_date = self.raw_dates[4 + i]
            date = self.convert_date(raw_date)
            new_daily_deaths.append((date, data[i] - data[i - 1]))
        return new_daily_deaths

    def forecast(self, n):
        return n * 2 ** (self.lag / self.doubling_time)

    def make_forecasts(self):
        new_daily_deaths = self.recorded_deaths
        forecasts_list = []
        raw_recorded_dates = self.raw_dates[4 + self.start + self.lag:]
        converted_recorded_dates = [self.convert_date(day) for day in raw_recorded_dates]
        all_dates = converted_recorded_dates + self.pad_dates()
        for i in range(len(new_daily_deaths)):
            date = all_dates[i]
            n = new_daily_deaths[i][1]
            forecasts_list.append((date, self.forecast(n)))
        return forecasts_list

    def gather_and_smooth(self):
        forecasted_deaths = self.make_forecasts()
        recorded_deaths = self.recorded_deaths
        bad_indices = []
        for i in range(1, len(recorded_deaths)):
            record = recorded_deaths[i][1]
            last_record = recorded_deaths[i - 1][1]
            if record < last_record:
                bad_indices.append(i)
        forecasted_deaths = [forecasted_deaths[i] for i in range(len(forecasted_deaths)) if i not in bad_indices]
        recorded_deaths = [recorded_deaths[i] for i in range(len(recorded_deaths)) if i not in bad_indices]
        return recorded_deaths, forecasted_deaths

    def fit_last_period(self):
        recorded_cases = self.get_country(data_type='cases').values.tolist()[0][4 + self.start:]
        x = [i for i in range(self.lag)]
        start_index = len(recorded_cases) - self.lag
        linear_values = recorded_cases[start_index:]
        fitted_dates = [self.convert_date(day) for day in self.raw_dates[4 + self.start + start_index:]]
        log_values = [math.log(y) / math.log(10) for y in linear_values]
        y = np.array(log_values)

        a = np.vstack([x, np.ones(len(x))]).T

        solution = np.linalg.lstsq(a, y, rcond=None)

        fitted_dates = fitted_dates
        print(len(recorded_cases[-self.lag:]))
        print(len(fitted_dates))
        m, c = solution[0]
        doubling_time = math.log(2) / (m * math.log(10))
        m_heuristic = math.log(2) / (2.7 * math.log(10))
        fitted_cases = [10 ** (m * x + c) for x in x]
        heuristic_cases = [10 ** (m_heuristic * x + c) for x in x]
        fig, ax = plt.subplots()
        ax.plot(fitted_dates, fitted_cases, label='exponential fit to cases')
        ax.plot(fitted_dates, recorded_cases[-self.lag:], label='recorded cases')
        ax.plot(fitted_dates, heuristic_cases, label='exponential with R = 2.7')
        fig.autofmt_xdate()
        fig.subplots_adjust(left=0.15)
        date_form = mdates.DateFormatter('%m/%d')
        ax.xaxis.set_major_formatter(date_form)
        plt.legend()
        plt.yscale('log')
        ax.yaxis.set_major_formatter(ScalarFormatter())
        plt.ylabel('Confirmed cases')
        plt.savefig('exponential_fits.png',dpi=500)
        plt.show()
        plt.close()
        print('doubling time:', doubling_time)
        return fitted_dates, fitted_cases, doubling_time

    def plot(self):
        recorded_deaths, forecasted_deaths = self.gather_and_smooth()
        recorded_days = [x[0] for x in recorded_deaths]
        death_counts = [x[1] for x in recorded_deaths]
        forecasted_days = [x[0] for x in forecasted_deaths]
        predicted_deaths = [x[1] for x in forecasted_deaths]
        fig, ax = plt.subplots()
        ax.plot(recorded_days, death_counts, label='recorded deaths')
        ax.plot(forecasted_days, predicted_deaths, label='forecasted deaths')
        fig.autofmt_xdate()
        fig.subplots_adjust(left=0.15)
        date_form = mdates.DateFormatter('%m/%d')
        ax.xaxis.set_major_formatter(date_form)
        plt.legend(loc=(0.6, 0.2))
        plt.yscale('log')
        ax.yaxis.set_major_formatter(ScalarFormatter())
        plt.ylabel('New deaths on each date')
        plt.ylim(top=10 ** 5)
        plt.savefig('death_forecasts_updated.png',dpi=500)
        plt.show()


forecast = DeathForecast('US')
forecast.plot()
