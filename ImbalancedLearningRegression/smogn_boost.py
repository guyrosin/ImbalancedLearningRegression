# load dependencies - third party
import numpy as np
import pandas as pd
import sklearn
import math
import smogn as smogn
from sklearn import tree
from sklearn import preprocessing
from sklearn.model_selection import train_test_split

# load dependencies - internal
from ImbalancedLearningRegression.phi import phi
from ImbalancedLearningRegression.phi_ctrl_pts import phi_ctrl_pts
from ImbalancedLearningRegression.over_sampling_gn import over_sampling_gn
from ImbalancedLearningRegression.gn import gn

# synthetic minority over-sampling technique for regression with gaussian noise with boost (based on SMOTEBoost using Adaboost)
# Look at https://github.com/nunompmoniz/ReBoost/blob/master/R/Functions.R

# ****need a train and a test set****
def smogn_boost(data, test_data, TotalIterations, pert, replace, k, y, error_threshold, rel_thres, samp_method = "balance"):

    # arguments/inputs
    
    # data: training set
    # test_data: test data
    # TotalIterations: user defined total number of iterations (pos int)
    # pert: perturbation / noise percentage
    # replace: sampling replacement (bool)
    # k: num of neighs for over-sampling (pos int)
    # y: response variable y by name (string)
    # error_threshold: user defined error threshold 
    # rel_thres: user defined relevance threshold 
    # samp_method: "balance or extreme" - sampling method is perc

    # split training data set into features and target
    ## store data dimensions
    n = len(test_data)
    d = len(test_data.columns)
      
    ## determine column position for response variable y
    y_col = test_data.columns.get_loc(y)
    
    ## move response variable y to last column
    if y_col < d - 1:
        cols = list(range(d))
        cols[y_col], cols[d - 1] = cols[d - 1], cols[y_col]
        data = data[test_data.columns[cols]]
    
    ## store original feature headers and
    ## encode feature headers to index position
    feat_names = list(test_data.columns)
    data.columns = range(d)
    
    ## sort response variable y by ascending order
    y = pd.DataFrame(test_data[d - 1])
    y_sort = y.sort_values(by = d - 1)
    y_sort = y_sort[d - 1]
    
    # set an initial iteration
    iteration = 1
    
    # Dt(i) set distribution as 1/m weights, which is length of data -1, as one of them is the target variable y 
    weights = 1/(len(data))
    dt_distribution = []
    for i in len(data):
        dt_distribution[i] = weights

    # calling phi control
    pc = phi_ctrl_pts (y=y, method="manual", xtrm_type = "both", coeff = 1.5, ctrl_pts=any)
    
    # calling only the control points (third value) from the output
    rel_ctrl_pts_rg = pc[2]
    
    # loop while iteration is less than user provided iterations
    while iteration <= TotalIterations:

        # this is the initial iteration of smogn, calculating it for the bumps, giving new data oversampled
        dt_over_sampled = smogn(data=data, y = y, k = 5, pert = pert, replace=replace, rel_thres = rel_thres, rel_method = "manual", rel_ctrl_pts_rg = rel_ctrl_pts_rg)

        # split oversampled data into a training and test set
        x = data[]
        y = data[]
        x_train, x_test, Y_train, Y_test = train_test_split(x, Y, test_size=0.3, random_state=1) # 70% training and 30% test

        # this is to call the decision tree and use it to achieve a new model, predict regression value for y (target response variable), and return the predicted values
        dt_model = tree.DecisionTreeRegressor()
        
        # check if I need to separate features and target
        dt_model = dt_model.fit(dt_over_sampled) 
        dt_data_predictions = dt_model.predict(y)

        # initialize error rate
        error = 0

        # calculate the error rate of the new model achieved earlier, as the delta between original dataset and predicted oversampled dataset
        # for each y in the dataset, calculate whether it is greater/lower than threshold and update accordingly
        error = abs((data[y] - dt_data_predictions[y])/data[y])
        
        for i in range(1, len[dt_data_predictions], 1):
            if error[i] > error_threshold:
                epsilon_t = epsilon_t + dt_distribution[i]
                                      
        # beta is the update parameter of weights based on the error rate calculated
        beta = pow(epsilon_t, 2)

        # update the distribution weights
        for i in dt_distribution:
            if error[i] <= error_threshold:
                dt_distribution[i] = dt_distribution[i] * beta
            else:
                dt_distribution[i] = dt_distribution[i]

        # normalize the distribution 
        dt_normalized = preprocessing.normalize(dt_distribution, max)

        # iteration count
        iteration = iteration + 1
        
        # calculation for weighted sum of all T models predictions, weights proportional to inverse error rates logarithm
        WeightSum = np.sum(dt_distribution)
        
    # **** need to modify original data after the whole loop ****
    
    
    return smogn_boost