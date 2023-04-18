from tensorflow.keras.utils import serialize_keras_object
from tensorflow.keras import utils
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
import json
start = datetime(2020, 1, 1)
end = datetime(2022, 1, 1)
qb = QuantBook()
symbol = qb.AddCrypto("BTCUSD", Resolution.Daily).Symbol
# symbol = qb.AddEquity("SPY", Resolution.Daily).Symbol
history = qb.History(symbol, start, end).loc[symbol]
history.head()
daily_pct_change = history[["open", "high", "low", "close", "volume"]].pct_change().dropna()
df = daily_pct_change
df.head()
indexes = df[((df.volume == float("inf")))].index
for i in indexes:
    df.at[i, "volume"] = max(df.volume.drop(indexes))
n_steps = 30
features = []
labels = []
for i in range(len(df)-n_steps):
    input_data = df.iloc[i:i+n_steps].values
    features.append(input_data)
    if df['close'].iloc[i+n_steps] >= 0.05:
        # UP
        label = 1
    else:
        # DOWN
        label = 0
    labels.append(label)
features = np.array(features)
labels = np.array(labels)
train_length = int(len(features) * 0.7)
X_train = features[:train_length]
X_test = features[train_length:]
y_train = labels[:train_length]
y_test = labels[train_length:]
# number of up vs down days in training data should be relatively balanced
sum(y_train)/len(y_train)
# use second part of data for training instead
test_length = int(len(features) * 0.3)
X_train = features[test_length:]
X_test = features[:test_length]
y_train = labels[test_length:]
y_test = labels[:test_length]
sum(y_train)/len(y_train)
model = Sequential([Dense(30, input_shape=X_train[0].shape, activation='relu'),
                    Dense(20, activation='relu'),
                    Flatten(),
                    Dense(1, activation='sigmoid')])
model.compile(loss='binary_crossentropy',
                optimizer='adam',
                metrics=['accuracy', 'mse'])
model.fit(X_train, y_train, epochs=100)
y_hat = model.predict(X_test)
results = pd.DataFrame({'y': y_test.flatten(), 'y_hat': y_hat.flatten()})
results.plot(title='Model Performance: predicted vs actual %change in closing price', figsize=(17, 7))
pred_train= model.predict(X_train)
scores = model.evaluate(X_train, y_train, verbose=0)
print('Accuracy on training data: {}% \n Error on training data: {}'.format(scores[1], 1 - scores[1]))

pred_test= model.predict(X_test)
scores2 = model.evaluate(X_test, y_test, verbose=0)
print('Accuracy on test data: {}% \n Error on test data: {}'.format(scores2[1], 1 - scores2[1]))

### Save Model
model_str = json.dumps(serialize_keras_object(model))
model_key = 'bitcoin_price_predictor'
qb.ObjectStore.Save(model_key, model_str)
### Load Model
if qb.ObjectStore.ContainsKey(model_key):
    model_str = qb.ObjectStore.Read(model_key)
    config = json.loads(model_str)['config']
    model = Sequential.from_config(config)
testDate = datetime.now()
df = qb.History(symbol, testDate - timedelta(40), testDate).loc[symbol]
df_change = df[["open", "high", "low", "close", "volume"]].pct_change().fillna(method="ffill").dropna()
df_change.replace([np.inf, -np.inf], 0., inplace=True)
model_input = []
for index, row in df_change.tail(30).iterrows():
    model_input.append(np.array(row))
model_input = np.array([model_input])
model.predict(model_input)
def predict_probabilities(model, input_data):
    predictions = model.predict(input_data)
    probabilities_up = []
    probabilities_down = []
    for i in range(101):
        probability_up = np.sum(predictions > i/100)/len(predictions)
        probability_down = np.sum(predictions < i/100)/len(predictions)
        probabilities_up.append(probability_up)
        probabilities_down.append(probability_down)
    return probabilities_up, probabilities_down

probabilities_up, probabilities_down = predict_probabilities(model, X_test)

"""
import matplotlib.pyplot as plt
# Grafik oluşturma
x = list(range(101)) # x eksenindeki değerler (yüzdelikler)
plt.plot(x, probabilities_up, label='Up') # up olasılıklarını grafiğe ekle
plt.plot(x, probabilities_down, label='Down') # down olasılıklarını grafiğe ekle
plt.xlabel('Yüzdelik') # x eksenine etiket ekle
plt.ylabel('Olasılık') # y eksenine etiket ekle
plt.title('Up/Down olasılıkları') # grafik başlığı
plt.legend() # legend'i göster
plt.show() # grafiği göster
"""
"""
plt.stem(probabilities_up, linefmt='blue', markerfmt='bo', label='Up probabilities')
plt.stem(probabilities_down, linefmt='red', markerfmt='ro', label='Down probabilities')
plt.xlabel('Percentage')
plt.ylabel('Probability')
plt.title('Up and Down Probabilities')
plt.legend()
plt.show()
"""
"""
percentages = [i for i in range(101)]

# iki ayrı scatter plot
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6))
ax1.scatter(percentages, probabilities_up, c='b', label='Up')
ax2.scatter(percentages, probabilities_down, c='r', label='Down')
ax1.set_xlabel('Percentage')
ax1.set_ylabel('Probability')
ax1.set_title('Up Probabilities')
ax1.legend()
ax2.set_xlabel('Percentage')
ax2.set_ylabel('Probability')
ax2.set_title('Down Probabilities')
ax2.legend()
plt.show()
"""
if model.predict(model_input)[0][0]*100 < 50:
    print("down")
    print(model.predict(model_input)[0][0]*100)
else:
    print("up")
    print(model.predict(model_input)[0][0]*100)

