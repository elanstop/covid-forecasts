# covid-forecasts
Inferring the numbers of deaths in weeks to come from growth over the past weeks

# Motivation
I have become concerned about uncertainty in epidemiological parameters of the pandemic being used to question the appropriateness of governments' responses. As I argue below, near-term forecasts can be made on the basis of parameters that are reasonably well constrained. 

# Data
Data is sourced from Johns Hopkins University's https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data/csse_covid_19_time_series

# Model
Let N be the number of deaths recorded today, D the true death rate, L the average lag between infection and death, and R the doubling time over the last L days. Then the true number of infections L days ago was N/D, the true number of infections today is N/D x 2^(L/R), and the predicted number of deaths L days from now is N/D x 2^(L/R) x D = N x 2^(L/R). Note that this value is independent of the death rate, which is uncertain due to insufficient testing. L is assumed to be 17 and R is obtained using a least-squares fit over the prior L days.


# Current Forecast
Note that as growth is estimated over the last 17 days and this is used to make the forecast, the last 17 days of the forecast are the most reliable.

![](death_forecasts_updated.png)
