
import os
import RPi.GPIO as GPIO
import time
from threading import Thread

# In Linux, Screen names should be 'pythonscreen' 'pythonimages'

pictures_directory = '/home/pi/StageDisplay/Pictures/'
deluxe_image_directory = '/home/pi/StageDisplay/SavedImages/deluxe.txt'
client_image_directory = '/home/pi/StageDisplay/SavedImages/client.txt'
dnd_image_directory = '/home/pi/StageDisplay/SavedImages/do_not_disturb.txt'
available_images_directory = '/home/pi/StageDisplay/SavedImages/all_images.txt'
primary_image_directory = '/home/pi/StageDisplay/SavedImages/primary.txt'
dlx_stored_img = ''
client_stored_img = ''
dnd_stored_img = ''
prim_stored_img = ''
primary_confirm = False
changes_waiting = False

led_on = False
button = 37
led = 11
hertz = 100  # We pulse at 100 Hertz
interval = 0.03  # Feel free to modify this interval to play with the pulsing speed
level = 5  # Controls the brightness in the following loop
lvlmax = 100
mod = 1  # Used to implement the pulsing instead of immediate switching
p = ''




def get_image_files(directory):
    '''Reads text doc that contains desired default images. Used to set variable.
    If the '''

    with open(directory) as file:
        file = file.read().strip("\n")
        if directory == prim_stored_img and file == '':
            file = dlx_stored_img
        return file


def display_picture(image_one, image_two):
    '''Launches FEH with primary and dnd image, switch_image function used to switch between the two.'''

    global pictures_directory

    os.system('DISPLAY=:0 screen -dm -S pythonimages feh --fullscreen --hide-pointer '
              + pictures_directory + image_one + ' ' + pictures_directory + image_two)

def switch_image():
    '''Sends a <space> command to the screen session 'pythonimages' which triggers FEH to switch to next image in
    slideshow.'''
    os.system('screen -r pythonimages -X stuff " "')

def save_load_images(directory, new_image_file):
    '''On user input, saves changes to default, client or dnd image to load'''

    with open(directory, 'w') as file:
        file.write(new_image_file + '\n')

def list_all_images(file_to_list):
    '''Lists all available files(images) in given directory.'''

    os.system('ls ' + pictures_directory + ' > ' + file_to_list)
    with open(file_to_list) as files:
        num = 1
        divider = ' - '
        for file in files:
            print(str(num) + divider + file)
            num += 1


def set_image(image_variable):
    '''User will choose an available picture file, also listed here, to set as the new default, client or dnd image. '''

    no_error = True

    if image_variable == dlx_stored_img:
        working_image = 'Deluxe'
        working_directory = deluxe_image_directory
        current_image = get_image_files(deluxe_image_directory)
    elif image_variable == client_stored_img:
        working_image = 'Client'
        working_directory = client_image_directory
        current_image = get_image_files(client_image_directory)
    elif image_variable == dnd_stored_img:
        working_image = 'Do No Disturb'
        working_directory = dnd_image_directory
        current_image = get_image_files(dnd_image_directory)
    else:
        no_error = False

    if no_error:
        print('\nThe current {} image is {}'.format(working_image, current_image))
        print('The available images are:\n')
        list_all_images(available_images_directory)
        choose_picture = int(input('\nFrom the list above, choose a number for the picture to set to the new {} image: '.format(
            working_image)))
        with open(available_images_directory) as all_files:
            new_file = all_files.readlines()
            with open(working_directory, 'w') as to_change_file:
                to_change_file.write(new_file[choose_picture - 1])
                change_primary = input('Would you like to make this the Primary image as well?: ').lower()
                if change_primary.startswith('y'):
                    set_primary(confirmed=True, image=new_file[choose_picture -1])
        clear_screen()
        restart_reminder()

    else:
        clear_screen()
        print('\nAn error occurred. Ask George where he fucked up.')



def set_primary(confirmed=False, image=None):

    global prim_stored_img
    global dlx_stored_img
    global client_stored_img

    if confirmed:
        with open(primary_image_directory, 'w') as primary:
            primary.writelines(image)
        restart_reminder()

    else:
        if primary_image == deluxe_image:
            confirm = input('Make {} the primary image?: '.format(client_image)).lower()
            if confirm.startswith('y') or confirm == 'yes':
                with open(client_image_directory) as client_image_change:
                    change_state = client_image_change.read()
                    with open(primary_image_directory, 'w') as primary:
                        primary.writelines(change_state.strip("\n"))
                clear_screen()
                restart_reminder()
            else:
                clear_screen()
                print('\tNo changes made.')
        elif primary_image == client_image:
            confirm = input('Make {} the primary image?: '.format(deluxe_image)).lower()
            if confirm.startswith('y') or confirm == 'yes':
                with open(deluxe_image_directory) as deluxe_image_change:
                    change_state = deluxe_image_change.read()
                    with open(primary_image_directory, 'w') as primary:
                        primary.writelines(change_state.strip("\n"))
                clear_screen()
                restart_reminder()
            else:
                clear_screen()
                print('\tNo changes made.')
        else:
            while True:
                print('\n-----------------------------------------------\n')
                print('There is no primary image currently set.')
                print("Let's change that.")
                print('1 - {}'.format(deluxe_image))
                print('2 - {}'.format(client_image))
                try:
                    choose_primary = int(input('Choose one of the images above: '))
                    if choose_primary == 1:
                        with open(primary_image_directory, 'w') as image_to_change:
                            image_to_change.writelines(deluxe_image)
                        clear_screen()
                        restart_reminder()
                        break
                    elif choose_primary == 2:
                        with open(primary_image_directory, 'w') as image_to_change:
                            image_to_change.writelines(client_image)
                        clear_screen()
                        restart_reminder()
                        break
                    else:
                        clear_screen()
                        print('You must make a valid selection.\n')

                except ValueError:
                    clear_screen()
                    print('You must choose a number.\n')



def led_loop():
    '''Controls led lights based on button press'''

    global level
    global mod
    global interval
    global p
    GPIO.add_event_detect(button, GPIO.FALLING, callback=led_on_off, bouncetime=200)

    while True:
        while led_on:
            p.start(2)  # We start at the low level (LED brightness will be lowest/off)
            # Modify the brightness
            level += mod

            # If max brightness or min brightness, revert direction
            if level >= lvlmax or level <= 2:
                mod *= -1

            # The duty cycle determines the percentage of time the
            # pin is switched on (we will perceive this as the LEDs
            # brightness)
            p.ChangeDutyCycle(level)

            # Wait
            time.sleep(interval)
        else:
            p.stop()
            GPIO.output(led, False)
            while not led_on:
                time.sleep(0.2)


def led_on_off(ev=None):
    '''Callback function for button press in led_loop. Changes state of led_on and displays the correct image
    accordingly
    '''

    global led_on
    led_on = not led_on
    switch_image()


def setup():
    global dlx_stored_img
    global client_stored_img
    global dnd_stored_img
    global prim_stored_img
    global p

    dlx_stored_img = get_image_files(deluxe_image_directory)
    client_stored_img = get_image_files(client_image_directory)
    dnd_stored_img = get_image_files(dnd_image_directory)
    prim_stored_img = get_image_files(primary_image_directory)

    global led
    global button
    global p
    global hertz

    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(led, GPIO.OUT)
    GPIO.setup(button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    p = GPIO.PWM(led, hertz)  # Initialize the software-PWM on our pin at the given rate of 100 Hertz


def clear_screen():
    os.system('clear')

def restart_reminder():
    global changes_waiting
    changes_waiting = True

    print('Changes have been saved.')
    print('You must quit and relaunch the program for changes to take effect.')


def user_interaction():
    clear_screen()

    while True:
        if changes_waiting:
            print('-------------------------------------------------------------')
            print('\t*** Changes Waiting ***')
        print('-------------------------------------------------------------')
        print('\nCurrent images:')
        print('\tPrimary: {}'.format(prim_stored_img))
        print('\tCurrent Deluxe: {}'.format(dlx_stored_img))
        print('\tCurrent Client: {}'.format(client_stored_img))
        print('\tCurrent Do Not Disturb: {}'.format(dnd_stored_img))
        print('\nPlease enter a number from the list.\n')

        print('1 - Set DELUXE picture.')
        print('2 - Set CLIENT picture.')
        print('3 - Set DO NOT DISTURB picture.')
        print('4 - Change primary picture.')
        print('5 - Close program.')
        print('\nTo leave this screen and keep the program running: ^A D')
        print('-------------------------------------------------------------')

        try:
            user_action = int(input('\nWhat would you like to do?: '))

            if user_action == 1:
                clear_screen()
                set_image(dlx_stored_img)

            elif user_action == 2:
                clear_screen()
                set_image(client_stored_img)

            elif user_action == 3:
                clear_screen()
                set_image(dnd_stored_img)

            elif user_action == 4:
                # clear_screen()
                set_primary()

            elif user_action == 5:
                destroy()
                os.system('killall python3')
            else:
                clear_screen()
                print('\n\t** Invalid Selection **\n')

        except ValueError:
            clear_screen()
            print('\n\t** Invalid Selection **\n')



def killall():
    os.system('killall feh')


def destroy():
    global p
    os.system('screen -S pythonimages -X quit')
    os.system('screen -S pythonscreen -X quit')
    GPIO.output(led, False)
    p.stop()
    GPIO.cleanup()


def main():
    global p
    try:
        setup()
        display_picture(prim_stored_img, dnd_stored_img)
        t1 = Thread(target=led_loop)
        t2 = Thread(target=user_interaction)
        t1.start()
        t2.start()
    except KeyboardInterrupt:
        destroy()




if __name__ == '__main__':
    main()
