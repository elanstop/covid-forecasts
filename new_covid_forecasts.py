import datetime
import math
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
from matplotlib.ticker import ScalarFormatter
import pickle

register_matplotlib_converters()


# NOTE: currently dropping days where the new deaths dropped because they reflect noise during this phase

class DeathForecast:

    def __init__(self, country, lag=14, reference=12, double_time = 2.7):
        #self.doubling_time = 2.7
        self.deaths = pd.read_csv('deaths_3_31.csv')
        self.cases = pd.read_csv('cases_3_31.csv')
        self.country = country
        self.lag = lag
        self.reference = reference
        self.death_time_series = self.get_country('deaths').values.tolist()[0][4:]
        #print('death time series:',self.death_time_series)
        self.case_time_series = self.get_country('cases').values.tolist()[0][4:]
        #print(self.time_series)
        self.start = self.find_start()
        #print(self.start)
        self.raw_dates = self.get_country().columns.values.tolist()[4:]
        #print([(self.raw_dates[i],self.case_time_series[i]) for i in range(len(self.case_time_series))])
        #self.converted_dates = self.convert_all_dates()
        self.recorded_deaths = self.get_new_daily_deaths()
        print(self.recorded_deaths)
        self.smoothed_deaths = self.smooth_daily_deaths()
        #self.fitted_dates, self.fitted_cases = self.fit_last_period()
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
            #date = self.convert_date(raw_date)
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

    def get_growth_factor(self,input_date):
        #print('-----')
        #print('input date:',input_date)
        input_index = self.raw_dates.index(input_date)
        start_index = input_index - self.lag
        final_value = self.case_time_series[input_index]
        #print('cases on this date:',final_value)
        initial_value = self.case_time_series[start_index]
        #print('date 17 days earlier:',self.raw_dates[start_index])
        #print('cases 17 days earlier:',initial_value)
        growth_factor = final_value/initial_value
        print('growth factor:',growth_factor)
        return growth_factor

    def make_forecasts(self):
        input_data = self.smoothed_deaths
        #input_data = self.recorded_deaths
        forecast_list = []
        i_list = []
        growth_factor_list = []
        for i in range(4,len(input_data)):
            print('-----')
            record = input_data[i]
            date = record[0]
            print('recorded date', date)
            num_deaths = record[1]
            growth_factor = self.get_growth_factor(date)
            growth_factor_list.append(growth_factor)
            i_list.append(i)
            predicted_deaths = num_deaths*growth_factor
            forecasted_date = self.convert_date(date) + datetime.timedelta(days=self.lag)
            print('forecasted date 17 days ahead:',forecasted_date)
            forecast_list.append((forecasted_date,predicted_deaths))
        plt.plot(i_list,growth_factor_list)
        plt.show()
        plt.close()
        return forecast_list

    def plot(self):
        records = self.smoothed_deaths
        #records = self.recorded_deaths
        forecasts = self.forecasts
        recorded_days = [self.convert_date(x[0]) for x in records]
        print(recorded_days)
        recorded_deaths = [x[1] for x in records]
        forecasted_days = [x[0] for x in forecasts]
        print(forecasted_days)
        forecasted_deaths = [x[1] for x in forecasts]

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
        plt.savefig('new_death_forecasts.png',dpi=500)
        plt.show()
        plt.close()


d = DeathForecast('US')
d.plot()





#     def forecast(self, n):
#         #return n * 2 ** (self.lag / self.doubling_time)
#
#     def make_forecasts(self):
#         deaths = self.smoothed_deaths
#         forecasts_list = []
#         raw_recorded_dates = self.raw_dates[4 + self.start + self.lag:]
#         converted_recorded_dates = [self.convert_date(day) for day in raw_recorded_dates]
#         all_dates = converted_recorded_dates + self.pad_dates()
#         for i in range(len(new_daily_deaths)):
#             date = all_dates[i]
#             n = new_daily_deaths[i][1]
#             forecasts_list.append((date, self.forecast(n)))
#         return forecasts_list
#
#     def gather_and_smooth(self):
#         #forecasted_deaths = self.make_forecasts()
#         recorded_deaths = self.recorded_deaths
#         smoothed_recorded_deaths = [recorded_deaths[0]]
#         for i in range(1, len(recorded_deaths)):
#             record = recorded_deaths[i][1]
#             last_record = recorded_deaths[-1][1]
#             if record < last_record:
#                 continue
#             else:
#                 smoothed_recorded_deaths.append(recorded_deaths[i])
#         return smoothed_recorded_deaths
#
#         #bad_indices = []
#         # for i in range(1, len(recorded_deaths)):
#         #     record = recorded_deaths[i][1]
#         #     last_record = recorded_deaths[i - 1][1]
#         #     if record < last_record:
#         #         bad_indices.append(i)
#         # forecasted_deaths = [forecasted_deaths[i] for i in range(len(forecasted_deaths)) if i not in bad_indices]
#         # recorded_deaths = [recorded_deaths[i] for i in range(len(recorded_deaths)) if i not in bad_indices]
#         #return recorded_deaths, forecasted_deaths
#         return smoothed_record_deaths
#
#     def fit_last_period(self,input_date):
#         recorded_cases = self.get_country(data_type='cases').values.tolist()[0][4 + self.start:]
#         x = [i for i in range(self.lag)]
#         start_index = len(recorded_cases) - self.lag
#         linear_values = recorded_cases[start_index:]
#         fitted_dates = [self.convert_date(day) for day in self.raw_dates[4 + self.start + start_index:]]
#         #log_values = [math.log(y) / math.log(10) for y in linear_values]
#         #y = np.array(log_values)
#
#         #a = np.vstack([x, np.ones(len(x))]).T
#
#         #solution = np.linalg.lstsq(a, y, rcond=None)
#         scale_factors = []
#         for i in range(1,len(linear_values)):
#             factor = linear_values[i]/linear_values[i-1]
#             scale_factors.append(factor)
#         return scale_factors
#
#
#         # print(len(recorded_cases[-self.lag:]))
#         # print(len(fitted_dates))
#         # m, c = solution[0]
#         # doubling_time = math.log(2) / (m * math.log(10))
#         # m_heuristic = math.log(2) / (2.7 * math.log(10))
#         # fitted_cases = [10 ** (m * x + c) for x in x]
#         # heuristic_cases = [10 ** (m_heuristic * x + c) for x in x]
#         # fig, ax = plt.subplots()
#         # ax.plot(fitted_dates, fitted_cases, label='exponential fit to cases')
#         # ax.plot(fitted_dates, recorded_cases[-self.lag:], label='recorded cases')
#         # ax.plot(fitted_dates, heuristic_cases, label='exponential with R = 2.7')
#         # fig.autofmt_xdate()
#         # fig.subplots_adjust(left=0.15)
#         # date_form = mdates.DateFormatter('%m/%d')
#         # ax.xaxis.set_major_formatter(date_form)
#         # plt.legend()
#         # plt.yscale('log')
#         # ax.yaxis.set_major_formatter(ScalarFormatter())
#         # plt.ylabel('Confirmed cases')
#         # #plt.savefig('new_exponential_fits.png',dpi=500)
#         # plt.show()
#         # plt.close()
#         # print('doubling time:', doubling_time)
#         # return fitted_dates, fitted_cases, doubling_time
#
#     def plot(self):
#         recorded_deaths, forecasted_deaths = self.gather_and_smooth()
#         print(forecasted_deaths)
#         recorded_days = [x[0] for x in recorded_deaths]
#         death_counts = [x[1] for x in recorded_deaths]
#         forecasted_days = [x[0] for x in forecasted_deaths]
#         predicted_deaths = [x[1] for x in forecasted_deaths]
#         file = open('03_28_forecast.txt', 'wb')
#         pickle.dump(forecasted_deaths, file)
#         file.close()
#         fig, ax = plt.subplots()
#         ax.plot(recorded_days, death_counts, label='recorded deaths')
#         ax.plot(forecasted_days, predicted_deaths, label='forecasted deaths')
#         fig.autofmt_xdate()
#         fig.subplots_adjust(left=0.15)
#         date_form = mdates.DateFormatter('%m/%d')
#         ax.xaxis.set_major_formatter(date_form)
#         plt.legend(loc=(0.6, 0.2))
#         plt.yscale('log')
#         ax.yaxis.set_major_formatter(ScalarFormatter())
#         plt.ylabel('New deaths on each date')
#         plt.ylim(top=10 ** 5)
#         #plt.savefig('new_death_forecasts.png',dpi=500)
#         plt.show()
#
#
# forecast = DeathForecast('US')
# forecast.plot()
