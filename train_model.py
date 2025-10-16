import tensorflow as tf
import os
import matplotlib.pyplot as plt

# --- Configuration Parameters ---

# 1. Set the path to your main data directory
DATA_DIR = 'residuos'

# 2. Set the image size and other training parameters
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 20 # Start with 20 and increase if needed

# 3. Define the name for your final saved model file
MODEL_SAVE_PATH = 'keras_model.h5'
LABELS_SAVE_PATH = 'labels.txt'

# --- Step 1: Load and Prepare the Dataset ---

print("Loading and preparing dataset...")
# Use Keras's utility to load images from the directory structure.
# It automatically splits the data into training (80%) and validation (20%) sets.
train_dataset = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

validation_dataset = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

# Get the class names from the directory names
class_names = train_dataset.class_names
print(f"Found classes: {class_names}")

# Save the class names (labels) to a text file. This is important for your Django app.
with open(LABELS_SAVE_PATH, 'w') as f:
    for class_name in class_names:
        f.write(f"{class_name}\n")
print(f"Labels saved to {LABELS_SAVE_PATH}")


# Optimize performance by caching and prefetching data
train_dataset = train_dataset.cache().shuffle(1000).prefetch(buffer_size=tf.data.AUTOTUNE)
validation_dataset = validation_dataset.cache().prefetch(buffer_size=tf.data.AUTOTUNE)

# --- Step 2: Create a Data Augmentation Layer ---

# Data augmentation creates new training examples by altering existing ones (rotating, flipping, etc.).
# This helps the model generalize better to new, unseen images.
data_augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomFlip('horizontal'),
    tf.keras.layers.RandomRotation(0.2),
    tf.keras.layers.RandomZoom(0.2),
])

# --- Step 3: Build the Model using Transfer Learning ---

print("Building model with transfer learning...")
# 1. Load the pre-trained EfficientNetV2S model without its top classification layer.
#    'imagenet' weights are a great starting point for most computer vision tasks.
base_model = tf.keras.applications.EfficientNetV2S(
    input_shape=(*IMG_SIZE, 3),
    include_top=False,
    weights='imagenet'
)

# 2. Freeze the weights of the base model. We don't want to change what it has already learned.
base_model.trainable = False

# 3. Create the full model by adding our layers on top of the base model.
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(*IMG_SIZE, 3)),
    data_augmentation,
    # Wrap the function in a Lambda layer
    tf.keras.layers.Lambda(tf.keras.applications.efficientnet_v2.preprocess_input),
    base_model,
    
    # Flatten the output of the base model
    tf.keras.layers.GlobalAveragePooling2D(),
    
    # A dropout layer to prevent overfitting
    tf.keras.layers.Dropout(0.2),
    
    # The final prediction layer with one output neuron per class.
    # 'softmax' is used for multi-class classification.
    tf.keras.layers.Dense(len(class_names), activation='softmax')
])

# --- Step 4: Compile the Model ---

# Compile the model with an optimizer, loss function, and metrics.
model.compile(
    optimizer='adam',
    loss=tf.keras.losses.SparseCategoricalCrossentropy(),
    metrics=['accuracy']
)

# Print a summary of the model architecture
model.summary()


# --- Step 5: Train the Model ---

print(f"Starting training for {EPOCHS} epochs...")
history = model.fit(
    train_dataset,
    validation_data=validation_dataset,
    epochs=EPOCHS
)
print("Training finished.")

# --- Step 6: Evaluate the Model's Performance ---

# Plot the training and validation accuracy and loss
acc = history.history['accuracy']
val_acc = history.history['val_accuracy']
loss = history.history['loss']
val_loss = history.history['val_loss']

plt.figure(figsize=(8, 8))
plt.subplot(2, 1, 1)
plt.plot(acc, label='Training Accuracy')
plt.plot(val_acc, label='Validation Accuracy')
plt.legend(loc='lower right')
plt.ylabel('Accuracy')
plt.ylim([min(plt.ylim()), 1])
plt.title('Training and Validation Accuracy')

plt.subplot(2, 1, 2)
plt.plot(loss, label='Training Loss')
plt.plot(val_loss, label='Validation Loss')
plt.legend(loc='upper right')
plt.ylabel('Cross Entropy')
plt.ylim([0, 2.0])
plt.title('Training and Validation Loss')
plt.xlabel('epoch')
plt.savefig('training_history.png')
print("Training history plot saved to training_history.png")


# --- Step 7: Save the Final Model ---

print(f"Saving model to {MODEL_SAVE_PATH}...")
model.save(MODEL_SAVE_PATH)
print("Model saved successfully. ✅")