"""Hệ thống tính lương và thưởng nhân sự."""

from __future__ import annotations

import re
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Dict, Iterator, List, Optional, Union, overload

Number = Union[int, float, str, Decimal]


def _to_decimal(value: Number, name: str) -> Decimal:
    """Chuyển giá trị sang Decimal; từ chối bool, NaN, Infinity, chuỗi sai."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Decimal)):
        raise TypeError(f"{name} phải là số, nhận được {type(value).__name__}")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"{name} không phải là số hợp lệ: {value!r}") from None
    if not result.is_finite():
        raise ValueError(f"{name} phải là số hữu hạn")
    return result


def _require_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} không được rỗng")
    return value.strip()


def _require_non_negative(value: Number, name: str) -> Decimal:
    number = _to_decimal(value, name)
    if number < 0:
        raise ValueError(f"{name} không được âm (nhận {number})")
    return number


def format_money(value: Decimal) -> str:
    """18000000 -> '18.000.000 VND'."""
    return f"{value:,.0f}".replace(",", ".") + " VND"


@dataclass(frozen=True)
class BonusRecord:
    """Một khoản thưởng. Bất biến (frozen) để lịch sử không bị sửa lén.

    Quyết định thiết kế (A.5): LƯU LỊCH SỬ thay vì chỉ lưu tổng, vì kế toán cần
    truy vết "thưởng vì sao, bao nhiêu". Tổng thưởng được TÍNH từ lịch sử nên
    không thể bị lệch với chi tiết (một nguồn sự thật duy nhất).
    """
    amount: Decimal
    reason: str


class Employee(ABC):

    DEFAULT_DEPARTMENT = "Unassigned"

    @overload
    def __init__(self, employee_id: str, full_name: str) -> None: ...

    @overload
    def __init__(self, employee_id: str, full_name: str, department: str) -> None: ...

    def __init__(
        self,
        employee_id: str,
        full_name: str,
        department: str = DEFAULT_DEPARTMENT,
        monthly_bonus: Number = 0,
    ) -> None:
        self._employee_id = _require_text(employee_id, "Mã nhân sự")
        self._full_name = _require_text(full_name, "Họ tên")
        self._department = _require_text(department, "Phòng ban")
        self._bonus_history: List[BonusRecord] = []

        initial = _require_non_negative(monthly_bonus, "Thưởng")
        if initial > 0:
            self._bonus_history.append(BonusRecord(initial, "Thưởng ban đầu"))

    @property
    def employee_id(self) -> str:
        return self._employee_id

    @property
    def employeeId(self) -> str:
        return self._employee_id

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def fullName(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, value: str) -> None:
        self._full_name = _require_text(value, "Họ tên")

    @property
    def department(self) -> str:
        return self._department

    @property
    def departmentName(self) -> str:
        return self._department

    @department.setter
    def department(self, value: str) -> None:
        self._department = _require_text(value, "Phòng ban")

    @property
    def monthly_bonus(self) -> Decimal:
        return sum((r.amount for r in self._bonus_history), Decimal(0))

    @property
    def monthlyBonus(self) -> Decimal:
        return self.monthly_bonus

    @property
    def bonus_history(self) -> tuple:
        return tuple(self._bonus_history)

    @overload
    def add_bonus(self, amount: Number) -> Decimal: ...
    @overload
    def add_bonus(self, amount: Number, reason: str) -> Decimal: ...
    @overload
    def add_bonus(self, rate: Number, reference_amount: Number, reason: str) -> Decimal: ...

    def addBonus(self, *args):
        """Phương thức thích ứng với các phiên bản yêu cầu của đề bài."""
        return self.add_bonus(*args)

    def add_bonus(self, *args):
        """Phân phối theo số đối số: (amount), (amount, reason), (rate, reference_amount, reason)."""
        if len(args) == 1:
            return self._add_fixed_bonus(args[0])
        if len(args) == 2:
            return self._add_fixed_bonus(args[0], args[1])
        if len(args) == 3:
            return self._add_rate_bonus(args[0], args[1], args[2])
        raise TypeError(
            f"add_bonus nhận 1, 2 hoặc 3 đối số, nhưng nhận {len(args)}"
        )

    def _add_fixed_bonus(self, amount: Number, reason: Optional[str] = None) -> Decimal:
        value = _to_decimal(amount, "amount")
        if value <= 0:
            raise ValueError("amount phải lớn hơn 0")
        reason_text = "không nêu lý do" if reason is None else _require_text(reason, "reason")
        return self._record_bonus(value, reason_text)

    def _add_rate_bonus(self, rate: Number, reference_amount: Number, reason: str) -> Decimal:
        rate_value = _to_decimal(rate, "rate")
        reference = _to_decimal(reference_amount, "referenceAmount")
        if not (0 < rate_value <= Decimal("0.5")):
            raise ValueError("rate phải trong khoảng (0, 0.5]")
        if reference <= 0:
            raise ValueError("referenceAmount phải lớn hơn 0")
        reason_text = _require_text(reason, "reason")
        return self._record_bonus(rate_value * reference, reason_text)

    def _record_bonus(self, amount: Decimal, reason: str) -> Decimal:
        self._bonus_history.append(BonusRecord(amount, reason))
        return amount

    def reset_bonus(self) -> None:
        """Đặt lại thưởng khi bắt đầu kỳ lương mới."""
        self._bonus_history.clear()

    @abstractmethod
    def calculate_gross_pay(self) -> Decimal:
        """Thu nhập trước khấu trừ."""

    def calculateGrossPay(self) -> Decimal:
        return self.calculate_gross_pay()

    @abstractmethod
    def get_employee_type(self) -> str:
        """Tên loại nhân sự."""

    def getEmployeeType(self) -> str:
        return self.get_employee_type()

    def display_payroll_info(self) -> None:
        print(f"[{self.get_employee_type()}] {self.employee_id} - {self.full_name}"
              f" | Phòng: {self.department}")

    def displayPayrollInfo(self) -> None:
        self.display_payroll_info()

    def _display_bonus_and_total(self) -> None:
        for record in self._bonus_history:
            print(f"    + Thưởng: {format_money(record.amount)} ({record.reason})")
        print(f"    => Tổng thưởng: {format_money(self.monthly_bonus)}")
        print(f"    => Thu nhập : {format_money(self.calculate_gross_pay())}")

    def __repr__(self) -> str:
        return (f"{type(self).__name__}(id={self.employee_id!r}, "
                f"name={self.full_name!r}, dept={self.department!r})")


class SalariedEmployee(Employee):
    """Constructor rút gọn:  SalariedEmployee(id, name, monthly_salary)
       Constructor đầy đủ :  SalariedEmployee(id, name, monthly_salary,
                                responsibility_allowance, department, monthly_bonus)
    """

    def __init__(
        self,
        employee_id: str,
        full_name: str,
        monthly_salary: Number,
        responsibility_allowance: Number = 0,
        department: str = Employee.DEFAULT_DEPARTMENT,
        monthly_bonus: Number = 0,
    ) -> None:
        super().__init__(employee_id, full_name, department, monthly_bonus)
        self._monthly_salary = _require_non_negative(monthly_salary, "Lương tháng")
        self._responsibility_allowance = _require_non_negative(
            responsibility_allowance, "Phụ cấp trách nhiệm")

    @property
    def monthly_salary(self) -> Decimal:
        return self._monthly_salary

    @property
    def responsibility_allowance(self) -> Decimal:
        return self._responsibility_allowance

    def calculate_gross_pay(self) -> Decimal:
        return self._monthly_salary + self._responsibility_allowance + self.monthly_bonus

    def get_employee_type(self) -> str:
        return "Nhân viên lương cố định"

    def display_payroll_info(self) -> None:
        super().display_payroll_info()
        print(f"    + Lương tháng: {format_money(self._monthly_salary)}")
        print(f"    + Phụ cấp trách nhiệm: {format_money(self._responsibility_allowance)}")
        self._display_bonus_and_total()


class HourlyEmployee(Employee):
    """Constructor rút gọn:  HourlyEmployee(id, name, hourly_rate)   (số giờ = 0)
       Constructor đầy đủ :  HourlyEmployee(id, name, hourly_rate, worked_hours,
                                department, monthly_bonus)
    """

    STANDARD_HOURS = Decimal(160)
    MAX_HOURS = Decimal(250)
    OVERTIME_MULTIPLIER = Decimal("1.5")

    def __init__(
        self,
        employee_id: str,
        full_name: str,
        hourly_rate: Number,
        worked_hours: Number = 0,
        department: str = Employee.DEFAULT_DEPARTMENT,
        monthly_bonus: Number = 0,
    ) -> None:
        super().__init__(employee_id, full_name, department, monthly_bonus)
        self._hourly_rate = _require_non_negative(hourly_rate, "Đơn giá giờ")
        self._worked_hours = self._validate_hours(worked_hours)

    @classmethod
    def _validate_hours(cls, hours: Number) -> Decimal:
        value = _to_decimal(hours, "Số giờ làm")
        if not (0 <= value <= cls.MAX_HOURS):
            raise ValueError(f"Số giờ làm phải trong khoảng [0, {cls.MAX_HOURS}]")
        return value

    @property
    def hourly_rate(self) -> Decimal:
        return self._hourly_rate

    @property
    def worked_hours(self) -> Decimal:
        return self._worked_hours

    def set_worked_hours(self, hours: Number) -> None:
        self._worked_hours = self._validate_hours(hours)

    @property
    def regular_hours(self) -> Decimal:
        return min(self._worked_hours, self.STANDARD_HOURS)

    @property
    def overtime_hours(self) -> Decimal:
        return max(self._worked_hours - self.STANDARD_HOURS, Decimal(0))

    @property
    def base_pay(self) -> Decimal:
        return (self.regular_hours * self._hourly_rate
                + self.overtime_hours * self._hourly_rate * self.OVERTIME_MULTIPLIER)

    def calculate_gross_pay(self) -> Decimal:
        return self.base_pay + self.monthly_bonus

    def get_employee_type(self) -> str:
        if self._worked_hours > self.STANDARD_HOURS:
            return "Nhân viên theo giờ, có giờ vượt ngưỡng"
        return "Nhân viên theo giờ, không có giờ vượt ngưỡng"

    def display_payroll_info(self) -> None:
        super().display_payroll_info()
        print(f"    + Đơn giá giờ: {format_money(self._hourly_rate)}")
        print(f"    + Giờ thường: {self.regular_hours} | Giờ vượt ngưỡng: {self.overtime_hours}")
        print(f"    + Lương cơ sở: {format_money(self.base_pay)}")
        self._display_bonus_and_total()


class SalesEmployee(Employee):
    """Constructor rút gọn:  SalesEmployee(id, name, base_salary)
       Constructor đầy đủ :  SalesEmployee(id, name, base_salary, sales_revenue,
                                commission_rate, department, monthly_bonus)
    """

    MAX_COMMISSION_RATE = Decimal("0.3")

    def __init__(
        self,
        employee_id: str,
        full_name: str,
        base_salary: Number,
        sales_revenue: Number = 0,
        commission_rate: Number = 0,
        department: str = Employee.DEFAULT_DEPARTMENT,
        monthly_bonus: Number = 0,
    ) -> None:
        super().__init__(employee_id, full_name, department, monthly_bonus)
        self._base_salary = _require_non_negative(base_salary, "Lương cơ bản")
        self._sales_revenue = _require_non_negative(sales_revenue, "Doanh số")
        self._commission_rate = self._validate_rate(commission_rate)

    @classmethod
    def _validate_rate(cls, rate: Number) -> Decimal:
        value = _to_decimal(rate, "Tỷ lệ hoa hồng")
        if not (0 <= value <= cls.MAX_COMMISSION_RATE):
            raise ValueError(f"Tỷ lệ hoa hồng phải trong khoảng [0, {cls.MAX_COMMISSION_RATE}]")
        return value

    @property
    def base_salary(self) -> Decimal:
        return self._base_salary

    @property
    def sales_revenue(self) -> Decimal:
        return self._sales_revenue

    @property
    def commission_rate(self) -> Decimal:
        return self._commission_rate

    def update_sales_revenue(self, new_revenue: Number) -> None:
        """Cập nhật doanh số có kiểm soát (không được âm)."""
        self._sales_revenue = _require_non_negative(new_revenue, "Doanh số")

    @property
    def commission(self) -> Decimal:
        return self._sales_revenue * self._commission_rate

    def calculate_gross_pay(self) -> Decimal:
        return self._base_salary + self.commission + self.monthly_bonus

    def get_employee_type(self) -> str:
        return "Nhân viên kinh doanh"

    def display_payroll_info(self) -> None:
        super().display_payroll_info()
        print(f"    + Lương cơ bản: {format_money(self._base_salary)}")
        print(f"    + Doanh số: {format_money(self._sales_revenue)}"
              f" x {self._commission_rate * 100:.1f}% = {format_money(self.commission)}")
        self._display_bonus_and_total()


class Payroll:
    def __init__(self, period: str) -> None:
        self._period = _require_text(period, "Kỳ lương")
        self._employees: Dict[str, Employee] = {}

    @property
    def period(self) -> str:
        return self._period

    def __len__(self) -> int:
        return len(self._employees)

    def __iter__(self) -> Iterator[Employee]:
        return iter(self._employees.values())

    def addEmployee(self, employee: Employee) -> None:
        self.add_employee(employee)

    def add_employee(self, employee: Employee) -> None:
        if not isinstance(employee, Employee):
            raise TypeError("Chỉ có thể thêm đối tượng Employee")
        if employee.employee_id in self._employees:
            raise ValueError(f"Mã nhân sự {employee.employee_id} đã tồn tại trong bảng lương")
        self._employees[employee.employee_id] = employee

    def findEmployee(self, employee_id: str) -> Optional[Employee]:
        return self.find_employee(employee_id)

    def find_employee(self, employee_id: str) -> Optional[Employee]:
        return self._employees.get(employee_id)

    def calculateTotalPayroll(self) -> Decimal:
        return self.calculate_total_payroll()

    def calculate_total_payroll(self) -> Decimal:
        return sum((e.calculate_gross_pay() for e in self), Decimal(0))

    def calculatePayrollByDepartment(self, department: str) -> Decimal:
        return self.calculate_payroll_by_department(department)

    def calculate_payroll_by_department(self, department: str) -> Decimal:
        key = _require_text(department, "Phòng ban").casefold()
        return sum((e.calculate_gross_pay() for e in self
                    if e.department.casefold() == key), Decimal(0))

    def findHighestPaidEmployee(self) -> Optional[Employee]:
        return self.find_highest_paid_employee()

    def find_highest_paid_employee(self) -> Optional[Employee]:
        """Trả None nếu bảng lương rỗng."""
        if not self._employees:
            return None
        return max(self, key=lambda e: e.calculate_gross_pay())

    def displayPayroll(self) -> None:
        self.display_payroll()

    def display_payroll(self) -> None:
        print(f"===== BẢNG LƯƠNG KỲ {self._period} =====")
        if not self._employees:
            print("(Bảng lương rỗng - chưa có nhân sự)")
            print(f"Tổng bảng lương: {format_money(Decimal(0))}")
            return
        for employee in self:
            employee.display_payroll_info()
            print()
        print(f"Tổng bảng lương: {format_money(self.calculate_total_payroll())}")
        top = self.find_highest_paid_employee()
        print(f"Thu nhập cao nhất: {top.full_name} "
              f"({format_money(top.calculate_gross_pay())})")


def ask(prompt: str, parser, default=None):
    """Hỏi lại cho đến khi nhập hợp lệ. Nếu có default, Enter để dùng giá trị mặc định."""
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            return parser(raw)
        except (ValueError, TypeError) as exc:
            print(f"  ! Dữ liệu không hợp lệ: {exc}")


def text_parser(name: str):
    return lambda raw: _require_text(raw, name)


def money_parser(name: str, positive: bool = False):
    """Tiền VND: có thể gõ 15000000 hoặc 15.000.000 / 15,000,000."""
    def parse(raw: str) -> Decimal:
        cleaned = re.sub(r"[.,_\s]", "", raw)
        value = _require_non_negative(cleaned, name)
        if positive and value <= 0:
            raise ValueError(f"{name} phải lớn hơn 0")
        return value
    return parse


def number_parser(name: str):
    """Số thực (giờ làm, ...): chấp nhận dấu , hoặc . làm dấu thập phân."""
    return lambda raw: _require_non_negative(raw.replace(",", "."), name)


def rate_parser(name: str):
    """Tỷ lệ: gõ 0.05 hoặc 5% đều được."""
    def parse(raw: str) -> Decimal:
        cleaned = raw.replace(",", ".")
        if cleaned.endswith("%"):
            return _to_decimal(cleaned[:-1], name) / 100
        return _to_decimal(cleaned, name)
    return parse


def choice_parser(low: int, high: int):
    def parse(raw: str) -> int:
        if not raw.isdigit() or not (low <= int(raw) <= high):
            raise ValueError(f"vui lòng nhập số từ {low} đến {high}")
        return int(raw)
    return parse


def _pick_employee(payroll: Payroll) -> Optional[Employee]:
    if len(payroll) == 0:
        print("  Bảng lương đang rỗng, hãy thêm nhân sự trước.")
        return None

    def parse(raw: str) -> Employee:
        found = payroll.find_employee(raw)
        if found is None:
            raise ValueError(f"không tìm thấy mã {raw!r}")
        return found
    return ask("Nhập mã nhân sự", parse)


def _ask_common(payroll: Payroll):
    def parse_new_id(raw: str) -> str:
        employee_id = _require_text(raw, "Mã nhân sự")
        if payroll.find_employee(employee_id) is not None:
            raise ValueError(f"mã {employee_id} đã tồn tại trong bảng lương")
        return employee_id

    employee_id = ask("Mã nhân sự", parse_new_id)
    name = ask("Họ tên", text_parser("Họ tên"))
    department = ask("Phòng ban", text_parser("Phòng ban"))
    return employee_id, name, department


def _finish_add(payroll: Payroll, employee: Employee) -> None:
    payroll.add_employee(employee)
    print("  Đã thêm nhân viên")


def add_salaried(payroll: Payroll) -> None:
    """Nhân viên lương cố định (+ thưởng cố định)."""
    employee_id, name, department = _ask_common(payroll)
    salary = ask("Lương tháng (VND)", money_parser("Lương tháng"))
    allowance = ask("Phụ cấp (VND)", money_parser("Phụ cấp"), default=Decimal(0))
    bonus = ask("Thưởng cố định (VND, Enter nếu không có)",
                money_parser("Thưởng"), default=Decimal(0))
    employee = SalariedEmployee(employee_id, name, salary, allowance, department)
    if bonus > 0:
        employee.add_bonus(bonus, "Thưởng cố định")
    _finish_add(payroll, employee)


def add_hourly(payroll: Payroll, overtime: bool) -> None:
    """Nhân viên theo giờ. overtime=False: không quá 160 giờ; True: trên 160 giờ."""
    limit = HourlyEmployee.STANDARD_HOURS

    def parse_hours(raw: str) -> Decimal:
        hours = HourlyEmployee._validate_hours(raw.replace(",", "."))
        if overtime and hours <= limit:
            raise ValueError(f"loại có giờ vượt ngưỡng phải làm trên {limit} giờ")
        if not overtime and hours > limit:
            raise ValueError(f"loại không có giờ vượt ngưỡng phải làm tối đa {limit} giờ")
        return hours

    employee_id, name, department = _ask_common(payroll)
    rate = ask("Đơn giá giờ (VND)", money_parser("Đơn giá giờ"))
    hours_prompt = (f"Số giờ làm (trên {limit} đến 250)" if overtime
                    else f"Số giờ làm (0 đến {limit})")
    hours = ask(hours_prompt, parse_hours)
    bonus = ask("Thưởng (VND, Enter nếu không có)", money_parser("Thưởng"),
                default=Decimal(0))
    employee = HourlyEmployee(employee_id, name, rate, hours, department)
    if bonus > 0:
        employee.add_bonus(bonus, "Thưởng")
    _finish_add(payroll, employee)


def add_sales(payroll: Payroll) -> None:
    """Nhân viên kinh doanh (+ thưởng theo tỷ lệ của một giá trị tham chiếu)."""
    def parse_bonus_rate(raw: str) -> Decimal:
        value = rate_parser("Tỷ lệ thưởng")(raw)
        if not (0 <= value <= Decimal("0.5")):
            raise ValueError("tỷ lệ thưởng phải trong khoảng [0, 0.5]")
        return value

    employee_id, name, department = _ask_common(payroll)
    base = ask("Lương cơ bản (VND)", money_parser("Lương cơ bản"))
    revenue = ask("Doanh số (VND)", money_parser("Doanh số"), default=Decimal(0))
    commission = ask("Hoa hồng (0 - 0.3, hoặc dạng 5%)",
                     lambda raw: SalesEmployee._validate_rate(rate_parser("Hoa hồng")(raw)),
                     default=Decimal(0))
    bonus_rate = ask("Thưởng theo tỷ lệ (vd 2%, Enter nếu không có)",
                     parse_bonus_rate, default=Decimal(0))
    employee = SalesEmployee(employee_id, name, base, revenue, commission, department)
    if bonus_rate > 0:
        reference = ask("Giá trị tham chiếu để tính thưởng (VND)",
                        money_parser("Giá trị tham chiếu", positive=True))
        employee.add_bonus(bonus_rate, reference, "Thưởng theo tỷ lệ")
    _finish_add(payroll, employee)


def menu_add_employee(payroll: Payroll) -> None:
    items = [
        ("Nhân viên lương cố định",                       add_salaried),
        ("Nhân viên theo giờ, không có giờ vượt ngưỡng",  lambda p: add_hourly(p, False)),
        ("Nhân viên theo giờ, có giờ vượt ngưỡng",        lambda p: add_hourly(p, True)),
        ("Nhân viên kinh doanh",                          add_sales),
    ]
    print("\n--- THÊM NHÂN VIÊN ---")
    for index, (title, _) in enumerate(items, start=1):
        print(f"  {index}. {title}")
    print("  0. Quay lại")
    choice = ask("Chọn loại nhân viên", choice_parser(0, len(items)))
    if choice != 0:
        items[choice - 1][1](payroll)


def menu_total_payroll(payroll: Payroll) -> None:
    print("\n--- TÍNH TỔNG LƯƠNG ---")
    if len(payroll) == 0:
        print("  Bảng lương đang rỗng")
        return

    total = payroll.calculate_total_payroll()
    print(f"  Tổng bảng lương: {format_money(total)}")

    departments: Dict[str, Decimal] = {}
    for employee in payroll:
        dept = employee.department
        departments[dept] = departments.get(dept, Decimal(0)) + employee.calculate_gross_pay()

    if departments:
        print("  Tổng theo phòng:")
        for dept, amount in departments.items():
            print(f"    - {dept}: {format_money(amount)}")


def menu_find_employee(payroll: Payroll) -> None:
    print("\n--- TÌM NHÂN VIÊN THEO MÃ ---")
    if len(payroll) == 0:
        print("  Bảng lương đang rỗng")
        return
    employee_id = ask("Nhập mã nhân sự", text_parser("Mã nhân sự"))
    employee = payroll.find_employee(employee_id)
    if employee is None:
        print(f"  Không tìm thấy nhân viên có mã {employee_id}")
        return
    employee.display_payroll_info()


def menu_highest_paid_employee(payroll: Payroll) -> None:
    print("\n--- NHÂN VIÊN CÓ THU NHẬP CAO NHẤT ---")
    employee = payroll.find_highest_paid_employee()
    if employee is None:
        print("  Bảng lương đang rỗng")
        return
    print(f"  {employee.full_name} ({employee.employee_id})")
    print(f"  Thu nhập: {format_money(employee.calculate_gross_pay())}")
    print(f"  Phòng ban: {employee.department}")


def menu_total_by_department(payroll: Payroll) -> None:
    print("\n--- TỔNG THEO PHÒNG BAN ---")
    if len(payroll) == 0:
        print("  Bảng lương đang rỗng")
        return
    department = ask("Nhập tên phòng ban", text_parser("Phòng ban"))
    total = payroll.calculate_payroll_by_department(department)
    print(f"  Tổng lương phòng {department}: {format_money(total)}")


def menu_update_employee_metrics(payroll: Payroll) -> None:
    print("\n--- CẬP NHẬT SỐ GIỜ HOẶC DOANH SỐ ---")
    if len(payroll) == 0:
        print("  Bảng lương đang rỗng")
        return
    employee_id = ask("Nhập mã nhân sự", text_parser("Mã nhân sự"))
    employee = payroll.find_employee(employee_id)
    if employee is None:
        print(f"  Không tìm thấy nhân viên có mã {employee_id}")
        return
    if isinstance(employee, HourlyEmployee):
        hours = ask("Số giờ làm trong tháng", number_parser("Số giờ làm"))
        employee.set_worked_hours(hours)
        print(f"  Đã cập nhật số giờ làm của {employee.full_name}: {employee.worked_hours} giờ")
    elif isinstance(employee, SalesEmployee):
        revenue = ask("Doanh số mới", money_parser("Doanh số"))
        employee.update_sales_revenue(revenue)
        print(f"  Đã cập nhật doanh số của {employee.full_name}: {format_money(employee.sales_revenue)}")
    else:
        print("  Nhân viên này không có số giờ làm hoặc doanh số cần cập nhật")


def menu_add_bonus_to_employee(payroll: Payroll) -> None:
    print("\n--- THÊM THƯỞNG CHO NHÂN VIÊN ---")
    if len(payroll) == 0:
        print("  Bảng lương đang rỗng")
        return
    employee_id = ask("Nhập mã nhân sự", text_parser("Mã nhân sự"))
    employee = payroll.find_employee(employee_id)
    if employee is None:
        print(f"  Không tìm thấy nhân viên có mã {employee_id}")
        return

    bonus_type = ask("Chọn dạng thưởng", choice_parser(1, 3))
    if bonus_type == 1:
        amount = ask("Nhập số tiền thưởng", money_parser("Số tiền thưởng", positive=True))
        reason = ask("Lý do thưởng (Enter nếu không có)", text_parser("Lý do thưởng"), default="")
        if reason:
            employee.add_bonus(amount, reason)
        else:
            employee.add_bonus(amount)
    elif bonus_type == 2:
        amount = ask("Nhập số tiền thưởng", money_parser("Số tiền thưởng", positive=True))
        reason = ask("Lý do thưởng", text_parser("Lý do thưởng"))
        employee.add_bonus(amount, reason)
    else:
        rate = ask("Tỷ lệ thưởng (vd 0.05 hoặc 5%)", rate_parser("Tỷ lệ thưởng"))
        if not (0 < rate <= Decimal("0.5")):
            raise ValueError("tỷ lệ thưởng phải trong khoảng (0, 0.5]")
        reference_amount = ask("Giá trị tham chiếu", money_parser("Giá trị tham chiếu", positive=True))
        reason = ask("Lý do thưởng", text_parser("Lý do thưởng"))
        employee.add_bonus(rate, reference_amount, reason)

    print(f"  Đã thêm thưởng cho {employee.full_name}. Tổng thưởng hiện tại: {format_money(employee.monthly_bonus)}")


def menu_reset_bonus(payroll: Payroll) -> None:
    print("\n--- ĐẶT LẠI THƯỞNG KHI SANG KỲ MỚI ---")
    if len(payroll) == 0:
        print("  Bảng lương đang rỗng")
        return
    employee_id = ask("Nhập mã nhân sự", text_parser("Mã nhân sự"))
    employee = payroll.find_employee(employee_id)
    if employee is None:
        print(f"  Không tìm thấy nhân viên có mã {employee_id}")
        return
    employee.reset_bonus()
    print(f"  Đã đặt lại thưởng cho {employee.full_name}.")


def menu_list_employees(payroll: Payroll) -> None:
    print("\n--- DANH SÁCH NHÂN VIÊN ---")
    if len(payroll) == 0:
        print("  (Chưa có nhân viên nào)")
        return
    for employee in payroll:
        employee.display_payroll_info()
        print()
    print(f"  Tổng số nhân viên: {len(payroll)}")


def main() -> None:
    print("=== HỆ THỐNG TÍNH LƯƠNG VÀ THƯỞNG NHÂN SỰ ===")
    payroll = Payroll("2026-09")

    menu = [
        ("Thêm nhân viên",                     menu_add_employee),
        ("Tính tổng lương",                    menu_total_payroll),
        ("Tìm nhân viên theo mã",              menu_find_employee),
        ("Nhân viên có thu nhập cao nhất",     menu_highest_paid_employee),
        ("Tổng theo phòng ban",               menu_total_by_department),
        ("Cập nhật số giờ / doanh số",         menu_update_employee_metrics),
        ("Thêm thưởng cho nhân viên",          menu_add_bonus_to_employee),
        ("Đặt lại thưởng khi sang kỳ mới",     menu_reset_bonus),
        ("In danh sách nhân viên",             menu_list_employees),
    ]
    while True:
        print("\n===== MENU CHÍNH =====")
        for index, (title, _) in enumerate(menu, start=1):
            print(f"  {index}. {title}")
        print("  0. Thoát")
        choice = ask("Chọn chức năng", choice_parser(0, len(menu)))
        if choice == 0:
            print("Tạm biệt!")
            return
        try:
            menu[choice - 1][1](payroll)
        except (ValueError, TypeError) as exc:
            print(f"  ! Lỗi: {exc}")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nĐã thoát chương trình.")