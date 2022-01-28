import pandas as pd

from config import DEFAULT_TABLE, N_SIMULATIONS, N_USERS, TRAINING_INTERVAL_DAYS, logger
from organization import Organization
from sql import QueryParams, db_connection, query_db_to_df


def create_records_into_db() -> None:
    """Create database records from Hoxhunt training."""
    dummy_organization = Organization(
        n_users=N_USERS, n_simulations=N_SIMULATIONS, training_interval_days=TRAINING_INTERVAL_DAYS
    )
    logger.info("Organization created: %s", dummy_organization)
    dummy_organization.do_training()
    logger.info("Organization has now been trained in Hoxhunt!")
    result = dummy_organization.get_result()
    result.to_sql(DEFAULT_TABLE, db_connection, if_exists="replace", index=None)


def get_data_with_query() -> pd.DataFrame:
    """Load records from the database into a DataFrame.

    Query to fetch the raw data if you want to inspect it:

    from config import TABLE_COLUMNS
    query_params = QueryParams(
        dimensions=["*"],
        table=DEFAULT_TABLE
    )
    query_db_to_df(query_params, result_columns=TABLE_COLUMNS)
    """
    # Select proportion of misses, fails and successes each day, order
    # dates in an ascending order. (Though the organization size seems
    # to be 100 in this case so instead of calculating percentages
    # the inner query would have sufficed. This should however work
    # in general as well if the organization size changes)
    query_params = QueryParams(
        dimensions = [
            "timestamp",
            "fail * 100.0 / (fail + success + miss) AS f_pct",
            "miss * 100.0 / (fail + success + miss) AS m_pct",
            "success * 100.0 / (fail + success + miss) AS f_pct",
        ],
        # Doing the inner query this way may be kind of janky and
        # same result could be achieved by manipulating the data frame
        # given by the inner query. However, I wanted to do the data
        # processing on the database side as much as possible +
        # didn't want to alter the querying code to keep things clear
        table = "(SELECT timestamp, "
                "COUNT(CASE WHEN outcome = 'FAIL' THEN 1 END) AS fail, "
                "COUNT(CASE WHEN outcome = 'SUCCESS' THEN 1 END) AS success, "
                "COUNT(CASE WHEN outcome = 'MISS' THEN 1 END) AS miss\n"
                f"FROM {DEFAULT_TABLE}\n"
                "GROUP BY timestamp\n"
                "ORDER BY timestamp ASC) InnerQuery",
        group_by = ["timestamp"],
        order_by = ["timestamp ASC"],
    )

    return query_db_to_df(query_params, result_columns=["timestamp", "Fail", "Miss", "Success"])


def main() -> None:
    """Run the entire simulation application."""
    create_records_into_db()
    logger.info("Training results successfully uploaded to the database")
    aggregated_data = get_data_with_query()
    logger.info("Aggregated training results have been fetched from the db.")
    csv_filename = "visualize.csv"
    aggregated_data.to_csv(csv_filename, index=False)
    logger.info("Data ready for visualization can be found in %s", csv_filename)


if __name__ == "__main__":
    main()
