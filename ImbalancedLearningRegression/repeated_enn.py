## load dependencies - third party
import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsClassifier

# load dependencies - internal
from ImbalancedLearningRegression.phi import phi
from ImbalancedLearningRegression.phi_ctrl_pts import phi_ctrl_pts
from ImbalancedLearningRegression.under_sampling_enn import under_sampling_enn
from ImbalancedLearningRegression.enn import enn


## majority under-sampling technique for regression with repeated edited nearest neighbor
def repeated_enn(
  
  ## main arguments / inputs
    data,                     ## training set (pandas dataframe)
    y,                        ## response variable y by name (string)
    samp_method = "balance",  ## over / under sampling ("balance" or extreme")
    drop_na_col = True,       ## auto drop columns with nan's (bool)
    drop_na_row = True,       ## auto drop rows with nan's (bool)
    max_iter = 100,           ## maximum iterations of enn algorithm (int)               
  
    ## phi relevance function arguments / inputs
    rel_thres = 0.5,          ## relevance threshold considered rare (pos real)
    rel_method = "auto",      ## relevance method ("auto" or "manual")
    rel_xtrm_type = "both",   ## distribution focus ("high", "low", "both")
    rel_coef = 1.5,           ## coefficient for box plot (pos real)
    rel_ctrl_pts_rg = None,   ## input for "manual" rel method  (2d array)

    ## KNeighborsClassifier attribute
    k = 3,                    ## the number of neighbors used for K-NN
    n_jobs = 1,               ## the number of parallel jobs to run for neighbors search

    ## user-defined KNeighborsClassifier
    k_neighbors_classifier = None  ## user-defined estimator allowing more non-default attributes
                                   ## will ignore k and n_jobs values if not None
  
    data_size = len(date)

    i = 0
    while i < max_iter{ #iterates calling enn on the updated dataset until either no more points can be removed or the maximum iterations have been reached
       new_enn = enn(
         data = data.copy(),
         y = this.y,
         samp_method=this.samp_method,
         rel_thres = this.rel_thres,
         k = this.k
       )
      
      if (len(new_enn) = data_size) { # nothing more can be removed from data set - end iterations and return new data
         return new_enn
      } else{
        
        data_size = len(new_enn) # update number of data points
        i++ # increment i
      }
         
         
    }
  
    return new_enn
    
    ):
