import tensorflow as tf

# Convert the model
converter = tf.lite.TFLiteConverter.from_saved_model("/home/wufisher/Xinan/data/test_model_path") # path to the SavedModel directory
converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS,
                                       tf.lite.OpsSet.SELECT_TF_OPS]
tflite_model = converter.convert()

# Save the model.
with open('model.tflite', 'wb') as f:
    f.write(tflite_model)