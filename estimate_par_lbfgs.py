from model.deepsurrogate import DeepSurrogate
import pandas as pd
import tensorflow as tf
import os
import tensorflow_probability as tfp
import numpy as np
import time
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib import style
style.use('fivethirtyeight')

deepsurrogate = DeepSurrogate()

path = "./results/table/"+deepsurrogate.par_c.name
path_graph = "./results/graphs/"+deepsurrogate.par_c.name
if os.path.exists(path) == False:
        os.makedirs(path)

if os.path.exists(path_graph) == False:
        os.makedirs(path_graph)
num = 1000
print(f"=== inverse modelling for {num} rows ===")
COL = ["alpha","delta","epsilon_b","epsilon_s","mu"]
COL_PLUS = COL + deepsurrogate.par_c.data.cross_vary_list
tf_loss = tf.keras.losses.MSE
data = deepsurrogate.X.iloc[:num,:]
data_y = deepsurrogate.Y.head(num)

# Each time, we initialize optimizer with the mean value of each parameter
# see to change with the mean saved
init_x = data[COL].mean().values

def func_g(x_params):
    # génial pour faire sur plusieurs colonnes la même valeur
    df[COL] = x_params.numpy()
    grad, mle = deepsurrogate.c_model.get_grad_and_mle(df[COL_PLUS],True)

    loss_value = np.mean(np.square(mle-y)**2)
    g = grad.mean()[COL].values

    g = tf.convert_to_tensor(g)
    loss_value = tf.convert_to_tensor(loss_value)

            #print('---',loss_value,flush=True)
    return loss_value, g

s = time.time()
list_of_ei = []

for i in tqdm(range(data.shape[0])):
    df = data.loc[i].to_frame().transpose()
    y = data["MLE"].loc[i]
            
    soln = tfp.optimizer.lbfgs_minimize(value_and_gradients_function=func_g, initial_position=init_x, max_iterations=50, tolerance=1e-60)
    pred_par = soln.position.numpy()
    obj_value = soln.objective_value.numpy()
            #print(soln,flush=True)
            
    # print(pred_par)
    e_i = np.abs(df[COL].values[0]-pred_par)/np.abs(deepsurrogate.X[COL].max()-deepsurrogate.X[COL].min())
    list_of_ei.append(e_i)
            #print(e_i)
            
soln_time = np.round((time.time() - s) / 60, 2)
print(soln_time)
df_ei = pd.DataFrame(list_of_ei)
print("=== Saving results ===")
df_ei.to_csv(path+"/ei_results.csv",index=False)

fig = plt.figure(figsize=(8,5))
plt.boxplot(df_ei)
plt.xticks([1, 2, 3,4,5], [r'$a$', r'$\delta$', r'$\mu$', r'$\epsilon_b$', r'$\epsilon_s$'])
#plt.title(r"Boxplot of $e_i$ by parameters")
plt.ylabel(r"$e_i$")
plt.xlabel(r"$x_i^*$")
plt.tight_layout()
plt.savefig(path_graph + f"/boxplot_ei_{deepsurrogate.par_c.name}.png")
plt.close()

df_ei_q = df_ei[df_ei <= df_ei.quantile(0.75)]
df_ei_q = df_ei_q.dropna()

fig = plt.figure(figsize=(8,5))
plt.boxplot(df_ei_q)
plt.xticks([1, 2, 3,4,5], [r'$a$', r'$\delta$', r'$\mu$', r'$\epsilon_b$', r'$\epsilon_s$'])
plt.ylabel(r"$e_i$")
plt.xlabel(r"$x_i^*$")
#plt.title(r"Boxplot of $e_i$ by parameters")
plt.tight_layout()
plt.savefig(path_graph + f"/boxplot_ei_q3_{deepsurrogate.par_c.name}.png")
plt.close()