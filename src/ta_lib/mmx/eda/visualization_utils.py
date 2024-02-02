import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, dcc, html
from jupyter_dash import JupyterDash
from plotly.subplots import make_subplots


def get_spend_vs_activity_plot_interact(
    data: pd.DataFrame, date_col: str, group_col: str = None, port: int = 8050
):
    """Create a plotting deck using the DataFrame generated from the "generate_spends_vs_activity_data" function.

    Parameters
    ----------
    data : pd.DataFrame
        Spend versus activity data generated by the "generate_spends_vs_activity_data" function.
    date_col : str
        Name of the column in the data containing the date.
    group_col : str, optional
        Name of the column in the data containing the group variable. Defaults to None.
    port : int, optional
        The port number on which the plot will be displayed. Defaults to 8050.

    Returns
    -------
    Dash
        Displays a Dash app containing the spend versus activity data plot and cost per activity plot.
    """

    app = JupyterDash(__name__)

    if group_col is None:
        app.layout = html.Div(
            [
                dcc.Dropdown(
                    id="touchpoint",
                    options=[
                        {"label": x, "value": x}
                        for x in data["variable_description"].unique()
                    ],
                    value=data["variable_description"].unique()[0],
                ),
                dcc.Dropdown(
                    id="activity",
                    options=[
                        {"label": x, "value": x} for x in data["activity_type"].unique()
                    ],
                    value=data["activity_type"].unique()[0],
                ),
                dcc.Dropdown(
                    id="plot_type",
                    options=[
                        {"label": x, "value": x}
                        for x in ["Scatter Plot", "Time Series"]
                    ],
                    value="Time Series",
                ),
                dcc.DatePickerRange(
                    id="date_range_picker",
                    min_date_allowed=data[date_col].min(),
                    max_date_allowed=data[date_col].max(),
                    start_date=data[date_col].min(),
                    end_date=data[date_col].max(),
                ),
                dcc.Graph(id="graph1"),
                dcc.Graph(id="graph2"),
            ]
        )

        @app.callback(
            Output("graph1", "figure"),
            Output("graph2", "figure"),
            Input("touchpoint", "value"),
            Input("activity", "value"),
            Input("plot_type", "value"),
            Input("date_range_picker", "start_date"),
            Input("date_range_picker", "end_date"),
        )
        def update_graph1(touchpoint, activity, plot_type, start_date, end_date):
            temp = data[
                (data["variable_description"] == touchpoint)
                & (data["activity_type"] == activity)
                & (data[date_col] >= start_date)
                & (data[date_col] <= end_date)
            ]

            temp["cost_per_act"] = temp["Spend"] / temp["Activity"]
            temp["cost_per_act"] = (
                temp["cost_per_act"].fillna(0).replace([np.inf, -np.inf], 0)
            )

            cpm_fig = px.line(temp, x=date_col, y="cost_per_act")
            cpm_fig.update_layout(title_text=" Cost per Activity ")
            cpm_fig.update_xaxes(title_text="Date")

            if plot_type == "Time Series":
                fig = make_subplots(specs=[[{"secondary_y": True}]])

                # Add traces
                fig.add_trace(
                    go.Scatter(x=temp[date_col], y=temp["Spend"], name="Spends"),
                    secondary_y=False,
                )

                fig.add_trace(
                    go.Scatter(x=temp[date_col], y=temp["Activity"], name="Activity"),
                    secondary_y=True,
                )

                # Add figure title
                fig.update_layout(title_text="Spends vs. Activity")

                # Set x-axis title
                fig.update_xaxes(title_text="Date")

                # Set y-axes titles
                fig.update_yaxes(title_text="<b>Spends</b>", secondary_y=False)
                fig.update_yaxes(title_text="<b>Activity</b>", secondary_y=True)

            elif plot_type == "Scatter Plot":
                fig = px.scatter(
                    temp,
                    x="Activity",
                    y="Spend",
                )
                fig.update_layout(title_text="Scatter plot Spends vs. Activity")
                fig.update_xaxes(title_text="Activity")
                fig.update_yaxes(title_text="Spend")

            return fig, cpm_fig

    else:
        app.layout = html.Div(
            [
                dcc.Dropdown(
                    id="touchpoint",
                    options=[
                        {"label": x, "value": x}
                        for x in data["variable_description"].unique()
                    ],
                    value=data["variable_description"].unique()[0],
                ),
                dcc.Dropdown(
                    id="activity",
                    options=[
                        {"label": x, "value": x} for x in data["activity_type"].unique()
                    ],
                    value=data["activity_type"].unique()[0],
                ),
                dcc.Dropdown(
                    id="plot_type",
                    options=[
                        {"label": x, "value": x}
                        for x in ["Scatter Plot", "Time Series"]
                    ],
                    value="Time Series",
                ),
                dcc.Dropdown(
                    id="geo",
                    options=[{"label": "Select all", "value": "all_values"}]
                    + [{"label": x, "value": x} for x in data[group_col].unique()],
                    value="all_values",
                    # multi=True
                ),
                dcc.DatePickerRange(
                    id="date_range_picker",
                    min_date_allowed=data[date_col].min(),
                    max_date_allowed=data[date_col].max(),
                    start_date=data[date_col].min(),
                    end_date=data[date_col].max(),
                ),
                dcc.Graph(id="graph1"),
                dcc.Graph(id="graph2"),
            ]
        )

        @app.callback(
            Output("graph1", "figure"),
            Output("graph2", "figure"),
            [
                Input("touchpoint", "value"),
                Input("activity", "value"),
                Input("plot_type", "value"),
                Input("geo", "value"),
                Input("date_range_picker", "start_date"),
                Input("date_range_picker", "end_date"),
            ],
        )
        def update_graph1(touchpoint, activity, plot_type, geo, start_date, end_date):
            if geo == "all_values":
                temp = data[
                    (data["variable_description"] == touchpoint)
                    & (data["activity_type"] == activity)
                    & (data[date_col] >= start_date)
                    & (data[date_col] <= end_date)
                ]
                temp = (
                    temp.groupby(
                        [
                            date_col,
                            "variable_activity_root",
                            "variable_description",
                            "activity_type",
                        ]
                    )
                    .sum(numeric_only=False)
                    .reset_index()
                )
            else:
                temp = data[
                    (data["variable_description"] == touchpoint)
                    & (data["activity_type"] == activity)
                    & (data[date_col] >= start_date)
                    & (data[date_col] <= end_date)
                ]
                temp = temp[temp[group_col] == geo]
                temp = (
                    temp.groupby(
                        [
                            date_col,
                            "variable_activity_root",
                            "variable_description",
                            "activity_type",
                        ]
                    )
                    .sum(numeric_only=False)
                    .reset_index()
                )

            temp["cost_per_act"] = temp["Spend"] / temp["Activity"]
            temp["cost_per_act"] = (
                temp["cost_per_act"].fillna(0).replace([np.inf, -np.inf], 0)
            )

            cpm_fig = px.line(temp, x=date_col, y="cost_per_act")
            cpm_fig.update_layout(title_text=" Cost per Activity ")
            cpm_fig.update_xaxes(title_text="Date")

            if plot_type == "Time Series":
                fig = make_subplots(specs=[[{"secondary_y": True}]])

                # Add traces
                fig.add_trace(
                    go.Scatter(x=temp[date_col], y=temp["Spend"], name="Spends"),
                    secondary_y=False,
                )

                fig.add_trace(
                    go.Scatter(x=temp[date_col], y=temp["Activity"], name="Activity"),
                    secondary_y=True,
                )

                # Add figure title
                fig.update_layout(title_text="Spends vs. Activity")

                # Set x-axis title
                fig.update_xaxes(title_text="Date")

                # Set y-axes titles
                fig.update_yaxes(title_text="<b>Spends</b>", secondary_y=False)
                fig.update_yaxes(title_text="<b>Activity</b>", secondary_y=True)

            elif plot_type == "Scatter Plot":
                fig = px.scatter(
                    temp,
                    x="Activity",
                    y="Spend",
                )
                fig.update_layout(title_text="Scatter plot Spends vs. Activity")
                fig.update_xaxes(title_text="Activity")
                fig.update_yaxes(title_text="Spend")

            return fig, cpm_fig

    # Run app and display datault inline in the notebook
    app.run_server(mode="inline", debug=True, port=port)


def get_spend_vs_activity_plot(
    spend_activity_data: pd.DataFrame,
    variable_description: str,
    activity_type: str,
    date_range=tuple(),
    date_col=str,
    group_col=None,
    group_value=None,
):
    """
    Generate a spend versus activity plot for a given activity type.

    Parameters
    ----------
    spend_activity_data : pd.DataFrame
        The dataframe containing the spend and activity data.
    variable_description : str
        The variable description of the activity on which spend versus activity plots need to be generated.
    activity_type : str
        The activity type for which plots need to be generated.
    date_range : tuple, optional
        The date range on which plots need to be generated. Format: (start_date, end_date).
        If not provided, the plot will include data for the entire available date range.
        Defaults to an empty tuple.
    date_col : str, optional
        The name of the column representing the dates in the dataframe.
    group_col : str
        The name of the column used to group the data.
    group_value : str, optional
        The specific value within the `group_col` column to filter the data.
        If provided, the data will be filtered to include only rows where `group_col` equals `group_value`.
        Defaults to None, which means no filtering based on the `group_col` will be applied.
        This can be useful when you want to analyze the quarterly spends for a specific subgroup within the data.

    Returns
    -------
    plt.Figure
        The line plots containing spend versus activity and cost per activity plot.

    Notes
    -----
    - The `group_value` can be useful when you want to analyze the spend versus activity relationship for a specific subgroup within
      the data.
    """
    if len(date_range) == 0:
        start_date = spend_activity_data[date_col].min()
        end_date = spend_activity_data[date_col].max()
    else:
        start_date = date_range[0]
        end_date = date_range[1]

    variable_descriptions = spend_activity_data["variable_description"].unique()
    if variable_description.lower() not in map(str.lower, variable_descriptions):
        print(
            "'{}' activity type is not available for the given variable\n\
        The availabale activities are: ".format(
                variable_description
            )
        )
        for variable in variable_descriptions:
            print(variable)
        return

    unique_activities = spend_activity_data[
        (
            spend_activity_data["variable_description"].str.lower()
            == variable_description.lower()
        )
    ]["activity_type"].unique()

    if activity_type.lower() not in map(str.lower, unique_activities):
        print(
            "'{}' activity type is not available for the given variable\n\
        The availabale activities are: ".format(
                activity_type
            )
        )
        for activity in unique_activities:
            print(activity)
        return

    if group_value is None:
        temp = spend_activity_data[
            (
                spend_activity_data["variable_description"].str.lower()
                == variable_description.lower()
            )
            & (
                spend_activity_data["activity_type"].str.lower()
                == activity_type.lower()
            )
            & (spend_activity_data[date_col] >= start_date)
            & (spend_activity_data[date_col] <= end_date)
        ]
    else:
        temp = spend_activity_data[
            (
                spend_activity_data["variable_description"].str.lower()
                == variable_description.lower()
            )
            & (
                spend_activity_data["activity_type"].str.lower()
                == activity_type.lower()
            )
            & (spend_activity_data[date_col] >= start_date)
            & (spend_activity_data[date_col] <= end_date)
            & (spend_activity_data[group_col] == group_value)
        ]

    temp["cost_per_act"] = temp["Spend"] / temp["Activity"]
    temp["cost_per_act"] = temp["cost_per_act"].fillna(0).replace([np.inf, -np.inf], 0)
    fig = make_subplots(
        rows=2,
        cols=1,
        specs=[[{"secondary_y": True}], [{}]],
        subplot_titles=(
            "Spends vs. Activity ---> {}".format(variable_description),
            " Cost per Activity for {} ".format(activity_type),
        ),
    )

    # Add traces
    fig.add_trace(
        go.Scatter(x=temp[date_col], y=temp["Spend"], name="Spends"),
        secondary_y=False,
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            x=temp[date_col],
            y=temp["Activity"],
            name="Activity ({})".format(activity_type),
        ),
        secondary_y=True,
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(x=temp[date_col], y=temp["cost_per_act"], name="Cost_Per_Activity"),
        row=2,
        col=1,
    )

    fig.update_xaxes(title_text="Date", row=2, col=1)

    # Set x-axis title
    fig.update_xaxes(title_text="Date", row=1, col=1)

    # # Set y-axes titles
    fig.update_yaxes(
        title_text="<b>Spends</b>",
        title_font={"size": 12},
        secondary_y=False,
        row=1,
        col=1,
    )
    fig.update_yaxes(
        title_text="<b>Activity ({})</b>".format(activity_type),
        title_font={"size": 10},
        secondary_y=True,
        row=1,
        col=1,
    )
    plt.show()
    return fig


def get_quarterly_spends_plot_interact(
    data: pd.DataFrame, group_col: str = None, port: int = 8050
):
    """
    Create a plotting deck using the DataFrame generated from the "generate_quarterly_spends_data" function.

    Parameters
    ----------
    data : pd.DataFrame
        Input DataFrame containing quarterly spend data.
        This data is generated from the "generate_quarterly_spends_data" function.
    group_col : str, optional
        Name of the column in the data containing the group variable. Defaults to None.
    port : int, optional
        The port number on which the plot will be displayed. Defaults to 8050.

    Returns
    -------
    Dash
        Dash app containing the quarterly spend plot.
    """

    app = JupyterDash(__name__)

    if group_col is None:
        app.layout = html.Div(
            [
                dcc.Dropdown(
                    id="touchpoint",
                    options=[
                        {"label": x, "value": x}
                        for x in data["variable_description"].unique()
                    ],
                    value=data["variable_description"].unique()[0],
                ),
                dcc.Graph(id="graph1"),
            ]
        )

        @app.callback(
            Output("graph1", "figure"),
            Input("touchpoint", "value"),
        )
        def update_graph1(touchpoint):
            temp = data[(data["variable_description"] == touchpoint)]

            fig = px.line(temp, x="YEAR_QTR", y="value")
            fig.update_layout(title_text="Quarterly Spends")
            fig.update_xaxes(title_text="Year Quarter")
            fig.update_yaxes(title_text="Spend")

            return fig

    else:
        app.layout = html.Div(
            [
                dcc.Dropdown(
                    id="touchpoint",
                    options=[
                        {"label": x, "value": x}
                        for x in data["variable_description"].unique()
                    ],
                    value=data["variable_description"].unique()[0],
                ),
                dcc.Dropdown(
                    id="geo",
                    options=[{"label": "Select all", "value": "all_values"}]
                    + [{"label": x, "value": x} for x in data[group_col].unique()],
                    value="all_values",
                    # multi=True
                ),
                dcc.Graph(id="graph1"),
            ]
        )

        @app.callback(
            Output("graph1", "figure"),
            [
                Input("touchpoint", "value"),
                Input("geo", "value"),
            ],
        )
        def update_graph1(touchpoint, geo):
            if geo == "all_values":
                temp = data[(data["variable_description"] == touchpoint)]
                temp = temp.groupby(["YEAR_QTR"]).sum(numeric_only=False).reset_index()
            else:
                temp = data[(data["variable_description"] == touchpoint)]
                temp = temp[temp[group_col] == geo]
                temp = temp.groupby(["YEAR_QTR"]).sum(numeric_only=False).reset_index()

            fig = px.line(temp, x="YEAR_QTR", y="value")
            fig.update_layout(title_text="Quarterly Spends")
            fig.update_xaxes(title_text="Year Quarter")
            fig.update_yaxes(title_text="Spend")

            return fig

    # Run app and display datault inline in the notebook
    app.run_server(mode="inline", debug=True, port=port)


def get_quarterly_spends_plot(
    quarterly_spend_data: pd.DataFrame,
    group_col: str,
    spend_variable_description: str,
    group_value=None,
):
    """
    Create a quarterly spends plot.

    Parameters
    ----------
    quarterly_spend_data : pd.DataFrame
        The dataframe containing the quarterly spend data.
    group_col : str
        The name of the column used to group the data.
    spend_variable_description : str
        The variable description for which the plot needs to be generated.
    group_value : str, optional
        The specific value within the `group_col` column to filter the data.
        If provided, the data will be filtered to include only rows where `group_col` equals `group_value`.
        Defaults to None, which means no filtering based on the `group_col` will be applied.

    Returns
    -------
    plt.Figure
        The line plot representing the quarterly spends for the given spend variable name.

    Notes
    -----
    - The `group_value` can be useful when you want to analyze the quarterly spends for a specific subgroup within the data.
    """

    spend_variables = quarterly_spend_data["variable_description"].unique()
    if spend_variable_description.lower() not in map(str.lower, spend_variables):
        print(
            "'{}' activity type is not available for the given variable\n\
        The available activities are: ".format(
                spend_variable_description
            )
        )
        for variable in spend_variables:
            print(variable)
        return

    if group_value is None:
        temp = quarterly_spend_data[
            (quarterly_spend_data["variable_description"] == spend_variable_description)
        ]
        temp = temp.groupby(["YEAR_QTR"]).sum(numeric_only=False).reset_index()

    else:
        temp = quarterly_spend_data[
            (quarterly_spend_data["variable_description"] == spend_variable_description)
        ]
        temp = temp[temp[group_col] == group_value]
        temp = temp.groupby(["YEAR_QTR"]).sum(numeric_only=False).reset_index()
    fig = px.line(temp, x="YEAR_QTR", y="value")
    fig.update_layout(
        title_text="Quarterly Spends - {}".format(spend_variable_description)
    )
    fig.update_xaxes(title_text="Year Quarter")
    fig.update_yaxes(title_text="Spend")
    plt.show()
    return fig


def get_actual_vs_predicted_plot_interact(
    act_vs_preds: pd.DataFrame,
    date_col: str,
    group_col: str,
    dv_col: str,
    is_log: bool = True,
    port: int = 8050,
) -> go.Figure:
    """
    Create a line plot comparing actual values and predicted values.

    Parameters
    ----------
    act_vs_preds : pd.DataFrame
        Actual versus prediction dataframe.
        DataFrame containing the actual value, predicted value, date column, and group column.
    date_col : str
        The column name of the date variable.
    group_col : str
        The column name of the group variable.
    dv_col : str
        The name of the dependent variable.
    is_log : bool, optional
        Indicates if the dependent variable is log-transformed. Defaults to True.
    port : int, optional
        The port number on which the plot will be displayed. Defaults to 8050.

    Returns
    -------
    Dash
        Dash app containing a line plot comparing actual values and predicted values.
    """

    data = act_vs_preds.copy()

    if is_log is True:
        data["actuals"] = np.exp(data["actuals"])
        data["preds"] = np.exp(data["preds"])

    # Initialize the app
    app = JupyterDash(__name__)

    # Define the layout
    app.layout = html.Div(
        [
            html.P("Filter Group variable"),
            dcc.Dropdown(
                id="dropdown",
                options=[{"label": "Select All", "value": "select_all"}]
                + [{"label": g, "value": g} for g in data[group_col].unique()],
                value="select_all",
                style={"width": "50%"},
            ),
            dcc.Graph(id="line-plot"),
        ]
    )

    # Define the callback
    @app.callback(Output("line-plot", "figure"), [Input("dropdown", "value")])
    def update_figure(selected_g):
        if selected_g == "select_all":
            filtered_df = data.groupby(date_col).sum().reset_index()
        else:
            filtered_df = data[data[group_col] == selected_g]

        fig = px.line(
            filtered_df,
            x=date_col,
            y=["actuals", "preds"],
            color_discrete_sequence=["blue", "orange"],
        )

        fig.update_layout(
            title="Actuals vs Prediction", xaxis_title="Date", yaxis_title=f"{dv_col}"
        )

        return fig

    app.run_server(mode="inline", debug=True, port=port)


def get_actual_vs_predicted_plot(
    act_vs_preds: pd.DataFrame,
    date_col: str,
    dv_col: str,
    is_log=False,
    group_col: str = None,
    group_value=None,
):
    """
    Plot actuals versus predicted values for a given dataframe.

    Parameters
    ----------
    act_vs_preds : pd.DataFrame
        The dataframe containing the actual and predicted values.
    date_col : str
        The name of the column representing the dates.
    dv_col : str
        The name of the dependent variable to be displayed on the y-axis.
    is_log : bool, optional
        Indicates whether the values are in logarithmic scale (default is False).
    group_col : str, optional
        The name of the column used for grouping the data (default is None).
    group_value : str, optional
       The specific value within the `group_col` column to filter the data.
        If provided, the data will be filtered to include only rows where `group_col` equals `group_value`.
        Defaults to None, which means no filtering based on the `group_col` will be applied.


    Returns
    -------
    plt.Figure
        The line plot showing the actual versus predicted values.

    Raises
    ------
    ValueError
        If an invalid group column name is provided.

    Notes
    -----
    - If `group_value` is set to "all" or None, the data will be grouped by `date_col` and summed for all group values.
    """
    data = act_vs_preds.copy()

    if is_log is True:
        data["actuals"] = np.exp(data["actuals"])
        data["preds"] = np.exp(data["preds"])

    if group_value == "all" or group_value is None:
        filtered_df = data.groupby(date_col).sum().reset_index()
    else:
        try:
            filtered_df = data[data[group_col] == group_value]
            print(filtered_df)
        except Exception as e:  # noqa
            print("Please enter a valid group column name")

    fig = px.line(
        filtered_df,
        x=date_col,
        y=["actuals", "preds"],
        color_discrete_sequence=["blue", "orange"],
    )

    fig.update_layout(
        title="Actuals vs Prediction", xaxis_title="Date", yaxis_title=f"{dv_col}"
    )

    return fig
