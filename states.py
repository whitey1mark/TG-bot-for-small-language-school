from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    waiting_broadcast_message = State()
    waiting_user_phone = State()
    waiting_user_message = State()
    waiting_payment_amount = State()
    waiting_user_id = State()
    waiting_category_name = State()
    waiting_category_price = State()
    waiting_edit_category = State()
    waiting_delete_category = State()
    waiting_delete_user = State()
    waiting_delete_confirm = State()

class RegistrationStates(StatesGroup):
    waiting_for_surname = State()
    waiting_for_name = State()
    waiting_for_patronymic = State()
    waiting_for_gender = State()
    waiting_for_email = State()
    waiting_for_phone = State()

class EditProfileStates(StatesGroup):
    waiting_edit_choice = State()
    waiting_edit_surname = State()
    waiting_edit_name = State()
    waiting_edit_patronymic = State()
    waiting_edit_phone = State()