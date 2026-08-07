import numpy as np
import matplotlib.pyplot as plt
import sklearn as skl


class Perceptron(object):
    """ NN Classifier
    
    Parameters:
    ----------
    eta : float 
        Learning rate (between 0.0 and 1.0)
    n_iter : int
        Passes over the training dataset


    Attributes:
    -----------
    w_ : 1 Dimensional aray -> Weights after fitting
    errors_ : List - Number of misclassifications in every epoch
    shuffle: bool - shuffles training data every epoch to prevent cycles
    random_state: int - set random state for shuffling and initializing weights
    """

    def __init__(self, eta=0.01, n_iter=10, shuffle=True, random_state=None, standardize_input=True, gradient_descent=None ):
        self.eta = eta
        self.n_iter = n_iter

        self.w_initialized = False
        self.shuffle = shuffle
        self.standardize_input = standardize_input

        # None, regular, stochastic
        self.gradient_descent = gradient_descent

        # randomize training data?
        if random_state:
            from numpy.random import seed
            seed(random_state)
        
        plt.style.use('fivethirtyeight')
    
    # Decides whether to do regular Gradient Descent, simple perceptron, stochastic GD
    def fit(self, X, y):
        self.w_ = np.zeros(1 + X.shape[1])

        # simple perceptron
        if self.gradient_descent == None:
            self._simple_perceptron(X,y)
       
        # The following is ADAptive LInear NEuron Classifier -- Adaline GD
        # Instead of updating the weights after evaluating each individual training, 
        # we calculate the gradient based on the whole training data via self.eta * errors.sum()
        # for the zero-weight and via self.eta * X.T.dot(errors) for the weights from 1 to m where
        # we do matrix-vector multiplication between our feature matrix and the error vector
        # aka batch GD
        elif self.gradient_descent == 'regular':
            self._gradient_fit(X,y)

        # Iterative or online GD. Large ML and batch GD can be costly; so instead of updating the weights based 
        # on the sum of the accumulated errors over all samples xi: (Delta)w=eta* sum(yi - activation(zi) )*xi,
        # we update the weights incrementally for each training sample: eta(yi - activation(zi) )*xi -- therefore
        # stochastic gradient is an approximation of GD but reaches convergnce much faster because of the more
        # frequent weight updates. Since each gradient is calculated based on a single training example, the error
        # surface is noisier than GD and this can be an advantage as stochastic GD can escape shallow local minima
        # To obtain accurate results in SGD, it is important to randomize (shuffle) the training data for every epoch
        # to prevent cyles. The fixed learning rate (eta) is often replaced by an adaptive rate which decreases over time.
        # Stochastic GD is also advantageous as online learning since the system can immediately adapt to changes and
        # the training data can be discarded after updating the model (depending on storage needs)
        elif self.gradient_descent == 'stochastic':
            self._stochastic_fit(X, y)
        
        else:
            print("Unknown optimization approach")
        
        return self

    # Perceptron convergence theorem: If 
    # (a) there exists parameter vector V such that
    # yi.transpose(V).xi/magnitude(T) >= epislon for all i; epislon is positive
    # (b) mag(xi) <= R where R is marigin
    # data set is linearly separable
    # Then the perceptron wil make at most (R/episoln)^2 mistakes
    def _simple_perceptron(self, X, y):
        self.errors_ = []
        
        # z=w0x0 + ... + wmxm = wT.x and phi(z) = 1 if z >=0 1 or -1
        for i_ in range(self.n_iter):
            err = 0
            #print(i_, "===================")
            for xi, target in zip(X,y):
                update = self.eta * (target - self.predict(xi))
                #print("xi = ", xi)
                self.w_[1:] += update * xi # mistake?
                self.w_[0] += update
                err += int(update != 0.0)
                #print("Error = ",err)
            self.errors_.append(err)
            
        return self

    # simple GD
    def _gradient_fit(self, X, y): 
        cost = 0
        self.cost_ = []

        for _ in range(self.n_iter):
            output = self.net_input(X)
            errors = (y - output)
            self.w_[1:] += self.eta * X.T.dot(errors)
            self.w_[0] += self.eta * errors.sum()
            cost = (errors**2).sum()/2.0
            self.cost_.append(cost)

        return self

    def _stochastic_fit(self, X, y):
        self.cost_ = []
        
        # If we want to update our model with streaming data, we call partial_fit() on individual
        # samples - self.partial_fit(X_std[0,:], y[0])

        for _ in range(self.n_iter):
            if self.shuffle:
                X, y = self._shuffle(X,y)
            cost = []
            for xi, target in zip(X,y):
                cost.append(self._update_weights(xi, target))

            avg_cost = sum(cost)/len(y)
            self.cost_.append(avg_cost)
        return self
    
    def _partial_fit(self, X, y):
        # Fit training data without reinitializing the weights
        if not self.w_initialized:
            self._initialize_weights(X.shape[1])
        if y.ravel().shape[0] > 1:
            for xi, target in zip(X,y):
                self._update_weights(xi, target)
        else:
            self._update_weights(X,y)
        return self
    
    def _initialize_weights(self, m):
        self.w_ = np.zeros(1 + m)
        self.w_initialized = True

    def _update_weights(self, xi, target):
        #Apply Adaline learning rule to update weights
        output = self.net_input(xi)
        error = (target - output)
        self.w_[1:] += self.eta * xi.dot(error)
        self.w_[0] += self.eta * error
        cost = 0.5 * error**2

        return cost
    
    def _activation(self, X):
        return self.net_input(X)
    
    def _shuffle(self, X, y):
        r = np.random.permutation(len(y))
        return X[r], y[r]
    
    ######################## Common Functionalities ###############################

    def get_raw_data_skl(self):
        print("Getting the Iris raw data using SKLearn Datasets...")

        from sklearn.datasets import load_iris
        iris_ds = load_iris()
        
        #X, y = load_iris(return_X_y=True)

        return iris_ds
    
    def generate_non_linear_data(self):
        print("Generating linearly unseparable random data")

        np.random.seed(0)

        X_xor = np.random.randn(200,2)
        y_xor = np.logical_xor(X_xor[:, 0] > 0, X_xor[:, 1] > 0)
        y_xor = np.where(y_xor, 1, -1)

        #print("your X_xor and y_xor arrays: ", X_xor)

        plt.scatter(X_xor[y_xor==1, 0], X_xor[y_xor==1,1], c='b', marker='x', label='1')
        plt.scatter(X_xor[y_xor==-1, 0], X_xor[y_xor==-1,1], c='r', marker='s', label='-1')
        plt.ylim(-3, 0)
        plt.legend()
        plt.show()
        
        return X_xor, y_xor
    
    def get_raw_data_pd(self):
        print("Getting the Iris raw data using Pandas/HTTP ...")
        import pandas as pd

        data_frame = pd.read_csv(
            'https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data', header=None)
        print("Done: get_raw_data()")

        return data_frame
    
    #===================== Common ML Funtionalities =================

    def net_input(self, X):
        #import sys as s
        #with open('file', 'w') as s.stdout:
        #    print("net_input()  self.w_[1:]: ",  self.w_[1:] )

        dot_prod = self.w_[0] + np.dot(X, self.w_[1:]) 

        return dot_prod

    def predict(self, X):
        #print("In Predict(): x = ", X)

        if(self.gradient_descent is None):
            y_hat = np.where(self.net_input(X) >= 0.0, 1, -1)
        else: # Used for both regular and Stochastic GD
            y_hat = np.where(self._activation(X) >= 0.0, 1, -1)
        
        return y_hat

    def model_lr_skl(self, X_train_std, y_train):
        print("Using Logistic Regression algorithm from SKL")

        from sklearn.linear_model import LogisticRegression

        lr = LogisticRegression(C=1000.0, random_state=0)

        model = lr.fit(X_train_std, y_train)

        print("Model Score = ", model.score(X_train_std, y_train))
        
        return model
    
    def model_svm_linear_skl(self, X_train_std, y_train):
        print("Using Support Vector Machine (SVM) algorithm from SKL")

        from sklearn.svm import LinearSVC
        # kernel = linear
        lsvc = LinearSVC(C=1.0, random_state=0)

        model = lsvc.fit(X_train_std, y_train)

        print("Model Score = ", model.score(X_train_std, y_train))
        
        return model
    
    def model_svm_rbf_skl(self, X_train, y_train):
        print("Using Support Vector Machine (SVM) with RBF algorithm from SKL")

        from sklearn.svm import SVC

        # kernel = kernel
        lsvr = SVC(kernel='rbf', random_state=0, gamma=0.10, C=10.0)

        model = lsvr.fit(X_train, y_train)

        print("Model Score = ", model.score(X_train, y_train))
        
        return model
    
    def model_knn_skl(self, X_train, y_train):
        print("Using k-nearest neighbors algorithm from SKL")

        from sklearn.neighbors import KNeighborsClassifier
       
        knn = KNeighborsClassifier(n_neighbors=3, p=2, metric='minkowski')

        model = knn.fit(X_train, y_train)

        print("Model Score = ", model.score(X_train, y_train))
        
        return model
    
    def standardize(self, data):
        # This is in place standardization so no need to return
        print("Standardizing input data...")
        #X_std = np.copy(data)
        data[:,0] = (data[:,0] - data[:,0].mean())/data[:,0].std()
        data[:,1] = (data[:,1] - data[:,1].mean())/data[:,1].std()

    def plot_raw(self, data, markerX='x', markerY='y', labelX='x label', labelY='y label'):
        plt.scatter(data[:50, 0], data[:50, 1], color='red',
                    marker=markerY, label='setosa')
        plt.scatter(data[50:100, 0], data[50:100, 1], color='purple',
                    marker=markerX, label='versicolor')
        
        # Ignore the label arguments for now...
        labelx = 'sepal length [cm]'
        labely = 'sepal width [cm]'

        plt.xlabel(labelx)
        plt.ylabel(labely)
        plt.legend(loc='upper left')
        plt.show()

    # Plot convergence
    def plot_rate_of_convergence(self, x_axis, y_axis, title='X vs Y', labelX='Epochs', labelY='Number of misclassifications'):
        # plot(range(1, len(ppn.errors_)+1), ppn.errors_, marker='o')
        plt.plot(x_axis,y_axis,marker='o')
        plt.xlabel(labelX)
        plt.ylabel(labelY)
        plt.title(title)
        plt.show()

    def plot_decision_regions(self, X, y, labelx, labely, title='any', test_idx=None,  model=None):
        from matplotlib.colors import ListedColormap

        resolution=0.02
        markers = ('s', 'x', 'o', '^', 'v')
        colors = ('red', 'blue', 'orange', 'gray', 'cyan')

        cmap_ = ListedColormap(colors[:len(np.unique(y))])

        print("Shape of input data = ", X.shape)

        # Equally distribute the input data
        x1_min, x1_max = X[:, 0].min() - 1, X[:, 0].max() + 1
        x2_min, x2_max = X[:, 1].min() - 1, X[:, 1].max() + 1

        #print("x1_min, x1_max, x2_min, x2_max = ", x1_min, x1_max,x2_min, x2_max )

        # NOTE: This is a made up data to create a square mesh grid
        col0, col1 = np.meshgrid(np.arange(x1_min, x1_max, resolution), np.arange(x2_min, x2_max, resolution))

        print("Recreated data col1 len = ", len(col1))

        # the self object (perceptron) comes with the classifier method
        if model:
            #Z = model.predict(X)
            Z = model.predict(np.array([col0.ravel(), col1.ravel()]).T)
            print("Shape of predicted Z = ", Z.shape)
            Z = Z.reshape(col0.shape)
            print("Resahped Z on col0 = ", Z.shape)

        else:
            Z = self.predict(np.array([col0.ravel(), col1.ravel()]).T)
            print("Shape of predicted Z = ", Z.shape)
            Z = Z.reshape(col0.shape)
            print("Resahped Z on col0 = ", Z.shape)

        plt.contourf(col0, col1, Z, alpha=0.5, cmap=cmap_)
        
        plt.xlim(col0.min(), col0.max())
        plt.ylim(col1.min(), col1.max())

        # plot all samples
        for idx, cl in enumerate(np.unique(y)):
            #print("The idx and cl = ", idx, cl)
            plt.scatter(x=X[y == cl, 0], y=X[y == cl, 1],
                        alpha=0.8, c=cmap_(idx),
                        marker=markers[idx], label=cl)

        # highlight test samples
        if test_idx:
            X_test, _ = X[test_idx,:], y[test_idx]
            plt.scatter(X_test[:,0], X_test[:,1], c='black', alpha = 1.0, 
                        linewidths=1, marker = 'o',
                        s=55, label='Test Set')

        plt.xlabel(labelx)
        plt.ylabel(labely)
        plt.title(title)
        plt.legend(loc='upper left')
        plt.show()

##################################
### MIT: ML Class HW responses ###
##################################

def length(col_v):
    return np.sqrt(np.sum(np.square(col_v)))

def normalize(col_v):
    return np.divide(col_v, length(col_v))

# Take a list of vectors and return row vector
def rv(value_list):
   return np.array([value_list])

#Take a list of vectors and return row vector
def cv(value_list):
    return np.array([value_list]).reshape(-1,1)

# Hyperplane distance to a point.
# Function takes column vectors (d by 1) x and th (of the same dimension) 
# and scalar th0 and returns the signed perpendicular distance (as a 1 by 1 array) 
# from the hyperplane encoded by (th, th0) to x.
def signed_dist(x, th, th0):
    return (np.dot(th.T, x)+th0)/(np.sqrt(np.sum(np.square(th))))

# Which side of the hyperplane
def positive(x, th, th0):
    return np.sign(np.dot(x.T, th) + th0)

def array_mult(A, B):
    result_matrix = []
    for i in range(len(A)):
        row = []
        for j in range(len(B[0])):
            element = 0
            for k in range(len(B)):
                element += A[i][k] * B[k][j]
            row.append(element)
        result_matrix.append(row)
 
    return result_matrix


### MIT Done ###

def compute():
    from sklearn.model_selection import train_test_split

    # Note that the learnig rate, and epochs are also called hyperprameters of the Perceptron
    # or Adaline learning,
    eta = 0.001
    iterations = 40

    # Defaults => eta=0.01, n_iter=10, shuffle=True, random_state=None, gradient_descent=None
    perceptron = Perceptron(eta, iterations, shuffle=True, random_state=1, standardize_input=True, gradient_descent='regular' )

    # Get the raw Iris data from SKLearn
    data_set = perceptron.get_raw_data_skl()
    #X = data_set.data[:, [2,3]] # col2, col3: Petal len, Petal width
    X = data_set.data[:, [0,2]] # col0, col2: Sepal len, Petal len
    # The Classes: 0=setosa, 1=versicolor, 2=viginica
    y = data_set.target 
    
    #print('Classes: ',list(data_set.target_names))
    
    # Using Pandas
    #data_frame = perceptron.get_raw_data_pd()
    #print(data_frame.head())
    #X = data_frame.iloc[0:150, [0, 2]].values
    #y = data_frame.iloc[0:150, 4].values
    #y = np.where(y == 'Iris-setosa', -1, 1)
    #print("X values using pandas = ", X)
    # Plot the raw data
    perceptron.plot_raw(X, 'x', 'o')
    
    #print("Print X: ", X)
    #print("Print y: ", y)

    # Below we do feature scaling for optimal performance. Standardization gives our data a property 
    # of standard normal distribution (mean=0, sd=1)
    # Standardization changes the input data (X) in place so no need to create copy of X
    if perceptron.standardize_input:
        perceptron.standardize(X)    

    labelx = 'Sepal Length [cm]'
    labely = 'Petal length [cm]'

    # let us sample the data into test and train sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=0)
    
    X_combined = np.vstack((X_train, X_test)) # first axis after 1-D arrays of shape (N,) and gets reshaped to (1,N)
    y_combined = np.hstack((y_train, y_test)) # equivalent to concatenation along the second axis
    
    print("Fitting (modeling) data...")
    if(perceptron.gradient_descent is not None): # Using Gradient Descent algorithm
        print("Using Gradient Descent")

        if perceptron.gradient_descent == 'stochastic':
            print("...Stochastic Gradient Descent")

        # Using the Logistic Regression algorithm in SKL (which is really classification)
        #skl_model = perceptron.model_lr_skl(X_train, y_train)
        #perceptron.plot_decision_regions(X_combined, y_combined, labelx, labely, 
        #                                 'Adaline - Stochastic or Regular Gradient Descent', test_idx=range(105,150), model=skl_model)
        
        # Using the SVM algorithm in SKL
        #svm_model = perceptron.model_svm_linear_skl(X_train, y_train)
        #perceptron.plot_decision_regions(X_combined, y_combined, labelx, labely, 
        #                                 'Adaline - Stochastic or Regular Gradient Descent', test_idx=range(105,150), model=svm_model)
        
        
        # Below we use our own algorithm to do Logistic Regression
        perceptron.fit(X_train, y_train)
        # y-axis: Sum-squared Errors
        perceptron.plot_rate_of_convergence(range(1, len(perceptron.cost_) + 1), perceptron.cost_,'Adaline Learning Rate','Epochs','Average Cost')
 
        perceptron.plot_decision_regions(X_combined, y_combined, labelx, labely, 'Adaline - Stochastic or Regular Gradient Descent', 
                                         test_idx=range(105,150), model=None)

    else:
        print("Simple Perceptron")
        perceptron.fit(X_train, y_train)
    
        perceptron.plot_rate_of_convergence(range(1, len(perceptron.errors_) + 1), perceptron.errors_, 
                                            'Simple Percep Learning Rate','Epochs', 'Number of misclassifications' )
        perceptron.plot_decision_regions(X_combined, y_combined, labelx, labely, 'Simple Perceptron', test_idx=range(105,150))

    print("Done: Fitting Linearly Separable Data -- the Iris data")
    #print('================================')
   
    #print("Test: Fitting non-linear data")
    X_xor, y_xor = perceptron.generate_non_linear_data()

    #svm_rbf_model = perceptron.model_svm_rbf_skl(X_xor, y_xor)
    #perceptron.plot_decision_regions(X_xor, y_xor, labelx='X', labely='Y', title='Non-linear Data Fitting with SVM using RBF', model=svm_rbf_model)

    #print("Done: Fitting non-linear data via SVM+RBF")
    print('================================')

    knn_model = perceptron.model_knn_skl(X_xor, y_xor)
    perceptron.plot_decision_regions(X_xor, y_xor, labelx='X', labely='Y', title='Non-linear Data Fitting using KNN', model=knn_model)

    print("Fitting the non-linear data using KNN...")
    
compute()