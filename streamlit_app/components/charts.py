import plotly.express as px

def line_chart(df, x, y, title):
    fig = px.line(df, x=x, y=y, markers=True, title=title)
    fig.update_layout(margin=dict(l=10, r=10, t=40, b=10))
    return fig