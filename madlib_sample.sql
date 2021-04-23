--Just a couple of trivial examples to validate MADlib is working...

--Examples more or less ripped from here:
--http://madlib.apache.org/docs/latest/group__grp__train__test__split.html

--Create train and test sets from source data. 

DROP TABLE IF EXISTS ppp_sample_with_replacement_train, ppp_sample_with_replacement_test;

SELECT madlib.train_test_split(
                                'pd_pt_prices',    -- Source table
                                'ppp_sample_with_replacement',     -- Output table
                                0.5,       -- train_proportion
                                0.5,      -- Default = 1 - train_proportion = 0.5
                                NULL, -- Strata definition -- e.g., groups to compare (?)
                                'closing_date, pd_usd_pm, pt_usd_pm', -- Columns to output
                                TRUE,      -- Sample with replacement
                                TRUE);     -- Separate output tables

SELECT * FROM ppp_sample_with_replacement_train ORDER BY closing_date;

SELECT * FROM ppp_sample_with_replacement_test ORDER BY closing_date;
--------------------------------------------------------------------------------------------
--Produce a linear regression model on from input table and then use the model
--to view the residuals.                                                       

SELECT madlib.linregr_train (
   'pd_pt_prices',         -- source table
   'pd_pt_prices_model',   -- output model table
   'pt_usd_am',            -- dependent variable
   'ARRAY[1, pd_usd_am]'   -- independent variables
);

SELECT * FROM pd_pt_prices_model;

SELECT closing_date, pd_usd_am, pt_usd_am,
        madlib.linregr_predict ( ARRAY[1, pd_usd_am], m.coef ) as predict,
        pt_usd_am - madlib.linregr_predict ( ARRAY[1, pd_usd_am], m.coef ) as residual
FROM pd_pt_prices, pd_pt_prices_model m;
