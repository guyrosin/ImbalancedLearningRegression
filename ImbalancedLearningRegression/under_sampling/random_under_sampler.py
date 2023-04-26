## Third Party Dependencies
from tqdm   import tqdm
from numpy  import random, ndarray
from pandas import DataFrame, Series, concat

## Standard Library Dependencies
from typing import Any

## Internal Dependencies
from ImbalancedLearningRegression.under_sampling.base import BaseUnderSampler
from ImbalancedLearningRegression.utils import (
    SAMPLE_METHOD, 
    RELEVANCE_METHOD, 
    RELEVANCE_XTRM_TYPE,
    phi,
    phi_ctrl_pts
)

class RandomUnderSampler(BaseUnderSampler):
    """Class to perform the Random Undersampling Algorithm.
    
    Parameters
    ----------
    drop_na_row: bool, default = True
        Whether rows with Null values will be dropped in data set.

    drop_na_col: bool, default = True
        Whether columns with Null values will be dropped in data set.

    samp_method: SAMPLE_METHOD, default = SAMPLE_METHOD.BALANCE
        Sampling information to resample the data set.

        Possible choices are:

            ``SAMPLE_METHOD.BALANCE``: A balanced amount of resampling. The resampling percentage
                is determined by the 'average ratio of points to rare/majority intervals' to the
                particular interval's number of points.

            ``SAMPLE_METHOD.EXTREME``: A more extreme amount of resampling. The resampling percentage
                is determined by a more extreme (in terms of value) and complex ratio than BALANCE.

    rel_thresh: float, default = 0.5 must be in interval (0, 1]
        This is the threshold used to determine whether an interval is a minority or majority interval.

    rel_method: RELEVANCE_METHOD, default = RELEVANCE_METHOD.AUTO
        Whether minority and majority intervals will be determined using internally computed parameters
        or by using parameters further defined by the user.

        Possible choices are:

            ``RELEVANCE_METHOD.AUTO``: Intervals are determined without further user input.

            ``RELEVANCE_METHOD.MANUAL``: Intervals are determined by using pre-computed points provided
                by the user.

    rel_xtrm_type: RELEVANCE_XTRM_TYPE, default = RELEVANCE_XTRM_TYPE.BOTH
        Whether minority and majority intervals will include the head/tail ends samples of the distribution.

        Possible choices are:

            ``RELEVANCE_XTRM_TYPE.BOTH``: Will include all points in their respective intervals.

            ``RELEVANCE_XTRM_TYPE.HIGH``: Will include only centre and tail end in their respective intervals.

            ``RELEVANCE_XTRM_TYPE.LOW``: Will include only centre and head end in their respective intervals.

    rel_coef: int or float, default = 1.5, must be positive greater than 0
        The coefficient used in box_plot_stats to determine the different quartile points as part of the 
        different intervals calculations.

    rel_ctrl_pts_rg: (2D array of floats or int) or None, default = None
        The pre-computed control points used in the manual calculation of the intervals.
        Used only if rel_method is set to RELEVANCE_METHOD.MANUAL.
    
    replace: bool, default = False
        Whether the same sample can be reused when generating different synthetic samples.

    manual_perc: bool, default = False
        Whether the percentage of oversampling for minority intervals will be provided by the user.

    perc_undersampling: int or float, default = -1
        If manual_perc is set to true, this is the percentage of undersampling for majority intervals.
        Must be greater than 0 if manual_perc is set to True.
    """
    def __init__(
        self, 
        drop_na_row: bool = True, 
        drop_na_col: bool = True, 
        samp_method: SAMPLE_METHOD = SAMPLE_METHOD.BALANCE, 
        rel_thres: float = 0.5, 
        rel_method: RELEVANCE_METHOD = RELEVANCE_METHOD.AUTO, 
        rel_xtrm_type: RELEVANCE_XTRM_TYPE = RELEVANCE_XTRM_TYPE.BOTH, 
        rel_coef: float = 1.5, 
        rel_ctrl_pts_rg: list[list[float | int]] | None = None, 
        replace: bool = True, 
        manual_perc: bool = False,
        perc_undersampling: int| float = -1
    ) -> None:
        
        super().__init__(drop_na_row = drop_na_row, drop_na_col = drop_na_col, samp_method = samp_method,
        rel_thres = rel_thres, rel_method = rel_method, rel_xtrm_type = rel_xtrm_type, rel_coef = rel_coef, rel_ctrl_pts_rg = rel_ctrl_pts_rg)

        self.replace            = replace
        self.manual_perc        = manual_perc
        self.perc_undersampling = perc_undersampling

    def _validate_perc_undersampling(self) -> None:
        """Validates if perc_undersampling matches specifications when manual percentage is selected.
        """
        if self.manual_perc:
            if self.perc_undersampling == -1:
                raise ValueError("cannot proceed: require percentage of under-sampling if manual_perc == True")
            elif self.perc_undersampling <= 0:
                raise ValueError("percentage of under-sampling must be a positve real number")
            elif self.perc_undersampling >= 1:
                raise ValueError("percentage of under-sampling must be less than 1")

    def fit_resample(self, data: DataFrame, response_variable: str) -> DataFrame:
        
        ## Validate Parameters
        self._validate_relevance_method()
        self._validate_data(data = data)
        self._validate_response_variable(data = data, response_variable = response_variable)
        self._validate_perc_undersampling()

        ## Remove Columns with Null Values
        data = self._preprocess_nan(data = data)

        ## Create new DataFrame that will be returned and identify Minority and Majority Intervals
        new_data, response_variable_sorted = self._create_new_data(data = data, response_variable = response_variable)
        relevance_params = phi_ctrl_pts(
            response_variable = response_variable_sorted, 
            method            = self.rel_method,
            xtrm_type         = self.rel_xtrm_type,
            coef              = self.rel_coef,
            ctrl_pts          = self.rel_ctrl_pts_rg)
        relevances       = phi(response_variable = response_variable_sorted, relevance_parameters = relevance_params)
        intervals, perc  = self._identify_intervals(response_variable_sorted = response_variable_sorted, relevances = relevances)

        ## Undersample data
        new_data = self._undersample(data = new_data, indices = intervals, perc = perc)

        ## Reformat New Data and Return
        new_data = self._format_new_data(new_data = new_data, original_data = data, response_variable = response_variable)
        return new_data

    def _undersample(self, data: DataFrame, indices: dict[int, "Series[Any]"], perc: list[float]) -> DataFrame:
        
        ## Create New DataFrame to hold modified DataFrame
        new_data = DataFrame()

        for idx, pts in indices.items():

            ## no sampling
            if perc[idx] >= 1:
                ## simply return no sampling
                ## results to modified training set
                new_data = concat([data.loc[pts.index], new_data], ignore_index = True)

            ## under-sampling
            if perc[idx] < 1:
                
                ## undersample intervals
                ## considered 'majority'
                synth_data, pre_numerical_processed_data = self._preprocess_synthetic_data(data = data, indices = pts.index)
                synth_data = self._random_undersample(synth_data = synth_data, perc = perc[idx] if not self.manual_perc else self.perc_undersampling)
                synth_data = self._format_synthetic_data(data = data, synth_data = synth_data, pre_numerical_processed_data = pre_numerical_processed_data)
                
                ## concatenate under-sampling
                ## results to modified training set
                new_data = concat([synth_data, new_data], ignore_index = True)

        return new_data

    def _random_undersample(self, synth_data: DataFrame, perc: float) -> DataFrame:
        """Undersample a majority interval using the Random Undersampling Algorithm.

        Parameters
        ----------
        synth_data: DataFrame
            Pre-processed minority interval, ready to be oversampled.

        perc: float
            The percentage of oversampling that will be conducted on the minority interval.

        Returns
        -------
        synth_data: DataFrame
            DataFrame that contains the undersampled majority interval.

        """
        
        ## total number of samples to remove
        n_synth = int(len(synth_data) * perc)
        
        ## randomly index data by the number samples to remove
        r_index = random.choice(
            a = tuple(range(0, len(synth_data))), 
            size = n_synth, 
            replace = self.replace, 
            p = None
        )
        
        ## create null matrix to store resampled interval
        synth_matrix = ndarray(shape = (n_synth, len(synth_data.columns)))

        ## store data in the synthetic matrix, data indices are chosen randomly above
        count = 0 
        for i in tqdm(r_index, ascii = True, desc = "new_index"):
            for attr in range(len(synth_data.columns)):
                synth_matrix[count, attr] = (synth_data.iloc[i, attr])
            count = count + 1

        ## convert synthetic matrix to dataframe
        synth_data = DataFrame(synth_matrix)
        
        ## synthetic data quality check
        if sum(synth_data.isnull().sum()) > 0:
            raise ValueError("synthetic data contains missing values")

        return synth_data

    ## Define Setters and Getters for Random Under Sampler

    @property
    def replace(self) -> bool:
        return self._replace

    @replace.setter
    def replace(self, replace: bool) -> None:
        self._validate_type(value = replace, dtype = (bool, ), msg = f"replace should be a boolean. Passed: {replace}")
        self._replace = replace

    @property
    def manual_perc(self) -> bool:
        return self._manual_perc

    @manual_perc.setter
    def manual_perc(self, manual_perc: bool) -> None:
        self._validate_type(value = manual_perc, dtype = (bool, ), msg = f"manual_perc should be a boolean. Passed: {manual_perc}")
        self._manual_perc = manual_perc

    @property
    def perc_undersampling(self) -> int | float:
        return self._perc_undersampling

    @perc_undersampling.setter
    def perc_undersampling(self, perc_undersampling: int | float) -> None:
        self._validate_type(value = perc_undersampling, dtype = (float, int), msg = f"perc_undersampling should be a float or an int. Passed: {perc_undersampling}")
        self._perc_undersampling = perc_undersampling