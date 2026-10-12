import pandas as pd
from visualizations import risk_category_chart,risk_exposure_chart,top_exposure_chart,ageing_distribution_chart,risk_score_chart,regional_exposure_chart,regional_risk_chart

df=pd.read_csv("outputs/risk_analysis.csv")

fig1=risk_category_chart(df)
fig2=risk_exposure_chart(df)
fig3=top_exposure_chart(df)
fig4=ageing_distribution_chart(df)
fig5=risk_score_chart(df)
fig6=regional_exposure_chart(df)
fig7=regional_risk_chart(df)

fig1.show()
fig2.show()
fig3.show()
fig4.show()
fig5.show()
fig6.show()
fig7.show()

print("All visualizations generated successfully.")