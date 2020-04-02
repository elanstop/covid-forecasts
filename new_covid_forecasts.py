import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from pandas.plotting import register_matplotlib_converters
from matplotlib.ticker import ScalarFormatter
import pickle

register_matplotlib_converters()


# NOTE: currently dropping days where the new deaths dropped because they reflect noise during this phase

class DeathForecast:

    def __init__(self, country, lag=14, reference=12):
        self.deaths = pd.read_csv('deaths_3_31.csv')
        self.cases = pd.read_csv('cases_3_31.csv')
        self.country = country
        self.lag = lag
        self.reference = reference
        self.death_time_series = self.get_country('deaths').values.tolist()[0][4:]
        self.case_time_series = self.get_country('cases').values.tolist()[0][4:]
        self.start = self.find_start()
        self.raw_dates = self.get_country().columns.values.tolist()[4:]
        self.recorded_deaths = self.get_new_daily_deaths()
        self.smoothed_deaths = self.smooth_daily_deaths()
        self.forecasts = self.make_forecasts()

    @staticmethod
    def convert_date(date):
        return datetime.datetime.strptime(date, "%m/%d/%y").date()

    def convert_all_dates(self):
        raw_dates = self.raw_dates
        converted_dates = []
        for i in range(len(raw_dates)):
            unconverted = raw_dates[i]
            converted = self.convert_date(unconverted)
            converted_dates.append(converted)
        return converted_dates

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
        data = self.death_time_series
        i = 0
        while data[i] < self.reference:
            i += 1
        return i

    def get_new_daily_deaths(self):
        data = self.death_time_series
        new_daily_deaths = []
        for i in range(self.start, len(data)):
            raw_date = self.raw_dates[i]
            new_daily_deaths.append((raw_date, data[i] - data[i - 1]))
        return new_daily_deaths

    def smooth_daily_deaths(self):
        recorded_deaths = self.recorded_deaths
        smoothed_recorded_deaths = [recorded_deaths[0]]
        for i in range(1, len(recorded_deaths)):
            record = recorded_deaths[i][1]
            last_record = smoothed_recorded_deaths[-1][1]
            if record < last_record:
                continue
            else:
                smoothed_recorded_deaths.append(recorded_deaths[i])
        return smoothed_recorded_deaths

    def get_growth_factor(self, input_date):
        input_index = self.raw_dates.index(input_date)
        start_index = input_index - self.lag
        final_value = self.case_time_series[input_index]
        initial_value = self.case_time_series[start_index]
        growth_factor = final_value / initial_value
        return growth_factor

    def make_forecasts(self):
        input_data = self.smoothed_deaths
        forecast_list = []
        i_list = []
        growth_factor_list = []
        for i in range(4, len(input_data)):
            record = input_data[i]
            date = record[0]
            num_deaths = record[1]
            growth_factor = self.get_growth_factor(date)
            growth_factor_list.append(growth_factor)
            i_list.append(i)
            predicted_deaths = num_deaths * growth_factor
            forecasted_date = self.convert_date(date) + datetime.timedelta(days=self.lag)
            forecast_list.append((forecasted_date, predicted_deaths))
        plt.plot(i_list, growth_factor_list)
        plt.show()
        plt.close()
        return forecast_list

    def plot(self):
        records = self.smoothed_deaths
        forecasts = self.forecasts
        recorded_days = [self.convert_date(x[0]) for x in records]
        recorded_deaths = [x[1] for x in records]
        forecasted_days = [x[0] for x in forecasts]
        forecasted_deaths = [x[1] for x in forecasts]
        file = open('03_31_forecast.txt', 'wb')
        pickle.dump(forecasted_deaths, file)
        file.close()
        fig, ax = plt.subplots()
        ax.plot(recorded_days, recorded_deaths, label='recorded deaths')
        ax.plot(forecasted_days, forecasted_deaths, label='forecasted deaths')
        fig.autofmt_xdate()
        fig.subplots_adjust(left=0.15)
        date_form = mdates.DateFormatter('%m/%d')
        ax.xaxis.set_major_formatter(date_form)
        plt.legend(loc=(0.6, 0.2))
        plt.yscale('log')
        ax.yaxis.set_major_formatter(ScalarFormatter())
        plt.ylabel('New deaths on each date')
        plt.ylim(top=10 ** 5)
        plt.savefig('new_death_forecasts.png', dpi=500)
        plt.show()
        plt.close()


d = DeathForecast('US')
d.plot()
