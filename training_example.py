from remote import *

if __name__ == '__main__':
    # init Remote with default config 
    r = Remote(SensorConfig(),
               ConnectionConfig(),
               TrainingConfig(_training_data_path='test_train_char/'),  # change training data path to some alternative name
               verbose=True)

    # send single byte to enable remote device
    r.send_ready_signal()

    # save 3 chars with some sample method config
    r.train_mode(char_sequence=['L', 'M', 'N'],
                 repeats=7,
                 include_extra_chars=False,
                 shuffle_chars=True)

    # go to keyboard_mode to test the training, requires prepare keyboard
    r.prepare_keyboard()
    # double clicking main button will exit
    r.keyboard_mode()

    # test here: RRqqrp