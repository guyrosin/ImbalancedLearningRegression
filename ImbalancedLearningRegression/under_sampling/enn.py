## Third Party Dependencies
from pandas                import DataFrame, Series, concat, Categorical, to_numeric, factorize
from sklearn.neighbors     import KNeighborsClassifier
from sklearn.preprocessing import MinMaxScaler

## Standard Library Dependencies
from typing import Any

## Internal Dependencies
from ImbalancedLearningRegression.utils.phi           import phi
from ImbalancedLearningRegression.utils.phi_ctrl_pts  import phi_ctrl_pts
from ImbalancedLearningRegression.utils.models        import SAMPLE_METHOD, RELEVANCE_METHOD, RELEVANCE_XTRM_TYPE
from ImbalancedLearningRegression.under_sampling.base import BaseUnderSampler

class ENN(BaseUnderSampler):

    def __init__(self, neighbour_classifier: KNeighborsClassifier, drop_na_row: bool = True, drop_na_col: bool = True, 
                 samp_method: SAMPLE_METHOD = SAMPLE_METHOD.BALANCE, rel_thres: float = 0.5, 
                 rel_method: RELEVANCE_METHOD = RELEVANCE_METHOD.AUTO, rel_xtrm_type: RELEVANCE_XTRM_TYPE = RELEVANCE_XTRM_TYPE.BOTH, 
                 rel_coef: float = 1.5, rel_ctrl_pts_rg: list[list[float | int]] | None = None, n_seed: int = 1) -> None:
        
        super().__init__(drop_na_row = drop_na_row, drop_na_col = drop_na_col, samp_method = samp_method,
        rel_thres = rel_thres, rel_method = rel_method, rel_xtrm_type = rel_xtrm_type, rel_coef = rel_coef, rel_ctrl_pts_rg = rel_ctrl_pts_rg)

        self.n_seed               = n_seed
        self.neighbour_classifier = neighbour_classifier

    def fit_resample(self, data: DataFrame, response_variable: str) -> DataFrame:
        
        # Validate Parameters
        self._validate_relevance_method()
        self._validate_data(data = data)
        self._validate_response_variable(data = data, response_variable = response_variable)

        # Remove Columns with Null Values
        data = self._preprocess_nan(data = data)

        # Create new DataFrame that will be returned and identify Minority and Majority Intervals
        new_data, response_variable_sorted = self._create_new_data(data = data, response_variable = response_variable)
        relevance_params = phi_ctrl_pts(response_variable = response_variable_sorted)
        relevances       = phi(response_variable = response_variable_sorted, relevance_parameters = relevance_params)
        intervals, perc  = self._identify_intervals(response_variable_sorted = response_variable_sorted, relevances = relevances)

        # Oversample Data
        new_data = self._undersample(data = new_data, indices = intervals, perc = perc)

        # Reformat New Data and Return
        new_data = self._format_new_data(new_data = new_data, original_data = data, response_variable = response_variable)
        return new_data

    def _undersample(self, data: DataFrame, indices: dict[int, "Series[Any]"], perc: list[float]) -> DataFrame:

        # Determine indices of minority samples
        minority_indices = [index for idx, indexes in indices.items() if perc[idx] >= 1 for index in indexes]

        # Create New DataFrame to hold modified DataFrame
        new_data = DataFrame()

        for idx, pts in indices.items():

            ## no sampling
            if perc[idx] >= 1:
                ## simply return no sampling
                ## results to modified training set
                new_data = concat([data.loc[pts.index], new_data], ignore_index = True)

            ## under-sampling
            if perc[idx] < 1:
                
                ## generate synthetic observations in training set
                ## considered 'minority'
                preprocessed_data, pre_numerical_processed_data = self._preprocess_data(data = data)
                undersampled_data = self._enn_undersample(data = preprocessed_data, majority_indices = pts.index.tolist(), minority_indices = minority_indices)
                undersampled_data = self._format_synthetic_data(data = data, synth_data = undersampled_data, 
                                                                pre_numerical_processed_data = pre_numerical_processed_data)
                
                ## concatenate over-sampling
                ## results to modified training set
                new_data = concat([undersampled_data, new_data], ignore_index = True)

        return new_data

    def _preprocess_data(self, data: DataFrame) -> tuple[DataFrame, DataFrame]:

        preprocessed_data = data.copy()

        ## find features without variation (constant features)
        feat_const = preprocessed_data.columns[preprocessed_data.nunique() == 1]

        ## temporarily remove constant features
        preprocessed_data = preprocessed_data.drop(feat_const, axis = 1)

        ## reindex features with variation
        for idx, column in enumerate(preprocessed_data.columns):
            preprocessed_data.rename(columns = { column : idx }, inplace = True)
        
        pre_numerical_processed_data = preprocessed_data.copy()

        ## create nominal and numeric feature list and
        ## label encode nominal / categorical features
        ## (strictly label encode, not one hot encode) 
        nom_dtypes = ["object", "bool", "datetime64"]

        for idx, column in enumerate(preprocessed_data.columns):
            if preprocessed_data[column].dtype in nom_dtypes:
                preprocessed_data.isetitem(idx, Categorical(factorize(preprocessed_data.iloc[:, idx])[0]))

        preprocessed_data = preprocessed_data.apply(to_numeric)

        return preprocessed_data, pre_numerical_processed_data

    def _enn_undersample(self, data: DataFrame, majority_indices: "list[Any]", minority_indices: "list[Any]") -> DataFrame:

        ## indices of results
        chosen_indices = []

        ## list representations
        data_X = data.iloc[:, :(len(data.columns) - 1)].values.tolist()
        class_y = [(1 if i in minority_indices else 0) for i in range(len(data))]

        ## loop through the majority set
        for i in majority_indices:
            train_X = data_X[:i] + data_X[i+1:]
            train_y = class_y[:i] + class_y[i+1:]
            min_max_scaler = MinMaxScaler()
            train_X_minmax = min_max_scaler.fit_transform(train_X)
            self.neighbour_classifier.fit(train_X_minmax, train_y)
            predict_X = min_max_scaler.transform(data.iloc[i,:(len(data.columns) - 1)].values.reshape(1,-1))
            predict_y = self.neighbour_classifier.predict(predict_X)
            if predict_y == 0:
                chosen_indices.append(i)

        ## conduct under sampling and store modified training set
        new_data = data.iloc[chosen_indices]

        return new_data

    # Define Setters and Getters for CNN

    @property
    def n_seed(self) -> int:
        return self._n_seed

    @n_seed.setter
    def n_seed(self, n_seed: int) -> None:
        self._validate_type(value = n_seed, dtype = (int, ), msg = f"n_seed should be an int. Passed: {n_seed}")
        self._n_seed = n_seed

    @property
    def neighbour_classifier(self) -> KNeighborsClassifier:
        return self._neighbour_classifier

    @neighbour_classifier.setter
    def neighbour_classifier(self, neighbour_classifier: KNeighborsClassifier) -> None:
        self._validate_type(value = neighbour_classifier, dtype = (KNeighborsClassifier, ), msg = f"neighbour_classifier should be an int. Passed Type: {type(neighbour_classifier)}")
        self._neighbour_classifier = neighbour_classifier

class RepeatedENN(ENN):

    def __init__(self, neighbour_classifier: KNeighborsClassifier, drop_na_row: bool = True, drop_na_col: bool = True, 
                 samp_method: SAMPLE_METHOD = SAMPLE_METHOD.BALANCE, rel_thres: float = 0.5, 
                 rel_method: RELEVANCE_METHOD = RELEVANCE_METHOD.AUTO, rel_xtrm_type: RELEVANCE_XTRM_TYPE = RELEVANCE_XTRM_TYPE.BOTH, 
                 rel_coef: float = 1.5, rel_ctrl_pts_rg: list[list[float | int]] | None = None, n_seed: int = 1,
                 max_iterations: int = 20) -> None:

        super().__init__(neighbour_classifier = neighbour_classifier, drop_na_row = drop_na_row, drop_na_col = drop_na_col, 
        samp_method = samp_method, rel_thres = rel_thres, rel_method = rel_method, rel_xtrm_type = rel_xtrm_type,
        rel_coef = rel_coef, rel_ctrl_pts_rg = rel_ctrl_pts_rg, n_seed = n_seed)

        self.max_iterations = max_iterations

    def fit_resample(self, data: DataFrame, response_variable: str) -> DataFrame:

        previous_size = len(data)
        previous_data = data.copy()
        successive_iter_without_undersampling = 0
        for i in range(self.max_iterations):
            new_data = super().fit_resample(data = previous_data, response_variable = response_variable)
            if len(new_data) == previous_size:
                successive_iter_without_undersampling += 1
                if successive_iter_without_undersampling == 5:
                    return new_data
            else:
                successive_iter_without_undersampling = 0
                
            previous_size = len(new_data)
            previous_data = new_data
        
        return previous_data            

    @property
    def max_iterations(self) -> int:
        return self._max_iterations

    @max_iterations.setter
    def max_iterations(self, max_iterations: int) -> None:
        self._validate_type(value = max_iterations, dtype = (int, ), msg = f"max_iterations must be an int. Passed: '{max_iterations}'")
        self._max_iterations = max_iterations