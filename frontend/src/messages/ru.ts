/**
 * Все тексты интерфейса.
 *
 * Строки взяты из словарей `ru` в макетах Claude Design без изменений —
 * так интерфейс не расходится с тем, что было согласовано в дизайне.
 * Проект одноязычный, поэтому это просто константы, без библиотеки i18n.
 */

export const nav = {
  contests: "Контесты",
  mySubmissions: "Мои работы",
  dashboard: "Админ-панель",
  login: "Войти",
  admin: "Админ",
  logout: "Выйти",
  menuOpen: "Открыть меню",
  menuClose: "Закрыть меню",
} as const;

export const landing = {
  liveBadge: "Контест №01 идёт прямо сейчас",
  emptyBadge: "Сейчас нет активного контеста",
  h1Line1: "Создавайте реальные продукты.",
  h1Line2: "Соревнуйтесь за реальные призы.",
  subhead:
    "CodeCup.tech — платформа контестов для разработчиков, которые доводят дело до конца. " +
    "Пришлите GitHub-репозиторий и живую демонстрацию — сообщество оценит вашу работу. " +
    "Использование ИИ приветствуется.",
  ctaViewContest: "Смотреть контест",
  ctaLoginTelegram: "Войти через Telegram",
  prizePoolLabelHero: "Призовой фонд",
  participantsLabelHero: "Участники",
  timeLeftHero: "Осталось времени",
  emptyStateTitle: "Сейчас нет активного контеста",
  emptyStateDesc:
    "Следующий контест CodeCup уже готовится. Войдите через Telegram, и мы сообщим вам, " +
    "как только он начнётся.",
  notifyMe: "Уведомить меня",
  notifyDone: "Мы вам сообщим",
  featuredLabel: "Контест недели",
  endsIn: "Осталось:",
  prizePool: "Призовой фонд",
  participants: "Участники",
  deadline: "Дедлайн",
  howItWorks: "Как это работает",
  step1Title: "Войдите через Telegram",
  step1Desc: "Один тап в Telegram — без паролей и форм.",
  step2Title: "Создайте и отправьте",
  step2Desc: "Соберите проект, затем отправьте GitHub, живую демонстрацию и видео.",
  step3Title: "Получите оценку и выиграйте",
  step3Desc: "Админы оценивают каждую заявку. Победители объявляются с призами.",
  footerCopy: "© 2026 CodeCup.tech — для разработчиков, которые доводят дело до конца.",
  footerLogin: "Войти",
  footerContest: "Контест",
} as const;

export const login = {
  title: "Вход в CodeCup",
  subtitle: "Без паролей и email. Мгновенная аутентификация через Telegram.",
  loginBtn: "Войти через Telegram",
  step1: "Нажмите кнопку «Войти через Telegram».",
  step2: "Подтвердите вход в приложении Telegram.",
  step3: "Вы будете перенаправлены обратно, уже авторизованным.",
  waitingTitle: "Подтвердите в Telegram",
  waitingDesc1: "Мы открыли чат с ботом CodeCup.",
  waitingDesc2: "Нажмите «Подтвердить вход» там, чтобы продолжить.",
  waitingSpinner: "Ожидание подтверждения…",
  openTelegram: "Открыть Telegram ещё раз",
  cancel: "Отмена",
  errorTitle: "Ссылка для входа устарела",
  errorDesc:
    "Время ожидания подтверждения в Telegram истекло. Пожалуйста, попробуйте войти снова.",
  retry: "Попробовать снова",
  notConfiguredTitle: "Вход временно недоступен",
  notConfiguredDesc: "Telegram-бот ещё не настроен. Попробуйте зайти немного позже.",
} as const;

export const contest = {
  notFoundTitle: "Контест не найден",
  notFoundDesc: "Возможно, контест удалён или ссылка неверна.",
  backHome: "На главную",
  allContests: "Все контесты",
  requirementsTitle: "Требования",
  yourSubmission: "Ваша заявка",
  prizePool: "Призовой фонд",
  participants: "Участники",
  worksTitle: "Работы участников",
  worksCta: "Рейтинг",
  worksEmpty: "Работ пока нет. Ваша может стать первой.",
  worksAll: "Смотреть все работы",
  worksCount: "работ",
  worksPageTitle: "Работы участников",
  worksBackToContest: "К контесту",
  worksRepo: "Репозиторий",
  worksDemo: "Демонстрация",
  worksVideo: "Видео",
  worksSubmittedAt: "Отправлено",
  worksClosedTitle: "Рейтинг ещё закрыт",
  worksClosedDesc:
    "Работы участников откроются после дедлайна — до этого никто не видит чужие " +
    "репозитории. Возвращайтесь, когда приём заявок закончится.",
  worksClosedOk: "Понятно",
  deadline: "Дедлайн",
  timeRemaining: "Осталось времени",
  endedOn: "Завершён",
  submitCta: "Отправить решение",
  closedCta: "Приём заявок закрыт",
  editCta: "Редактировать заявку",
  loginToSubmit: "Войдите, чтобы участвовать",
  live: "Идёт",
  ended: "Завершён",
  days: "ДНИ",
  hours: "ЧАС",
  minutes: "МИН",
  seconds: "СЕК",
} as const;

export const participation = {
  entryFee: "Взнос за участие",
  free: "Участие бесплатное",
  participateCta: "Участвовать",
  modalTitle: "Оплата участия",
  modalIntro: "Переведите взнос по реквизитам ниже и пришлите чек.",
  requisitesLabel: "Реквизиты",
  copied: "Скопировано",
  copy: "Скопировать",
  uploadLabel: "Загрузить чек",
  uploadHint: "Скриншот или PDF, до 10 МБ",
  chooseFile: "Выбрать файл",
  orSendViaBot: "или",
  sendViaBot: "Отправить чек через Telegram",
  waitingInBot: "Ждём ваш чек в Telegram-боте",
  waitingInBotHint: "Откройте бота и пришлите скриншот или PDF одним сообщением.",
  openBot: "Открыть бота",
  uploading: "Загружаем чек…",
  statusPending: "Чек на проверке",
  statusPendingHint: "Обычно это занимает немного времени. Мы сообщим в Telegram.",
  statusAccepted: "Взнос принят",
  statusAcceptedHint: "Можно отправлять решение.",
  statusRejected: "Чек отклонён",
  sendAnother: "Прислать другой чек",
  close: "Закрыть",
  payToParticipate: "Оплатить участие",
  loginToParticipate: "Войдите, чтобы участвовать",
  bannerPending: "Чек на проверке",
  bannerPendingHint: "Мы сообщим о решении в Telegram.",
  bannerAccepted: "Взнос принят",
  bannerAcceptedHint: "Можно отправлять решение.",
  bannerRejected: "Чек отклонён",
  bannerRejectedHint: "Пришлите другой чек.",
  bannerWaiting: "Ждём чек в Telegram-боте",
  bannerWaitingHint: "Откройте бота и пришлите скриншот или PDF.",
} as const;

export const submit = {
  heading: "Отправьте ваше решение",
  subheading:
    "Вы можете сохранить черновик и вернуться позже, до дедлайна. " +
    "Учитывается только последняя отправка до дедлайна.",
  githubLabel: "Ссылка на репозиторий GitHub",
  liveLabel: "Ссылка на живую демонстрацию",
  videoLabel: "Ссылка на демо-видео",
  descLabel: "Краткое описание",
  descPlaceholder: "Что вы создали и как это использует ИИ?",
  submitting: "Отправка вашего решения…",
  savingDraft: "Сохранение черновика…",
  draftSaved: "Черновик сохранён.",
  saveDraft: "Сохранить черновик",
  submitBtn: "Отправить решение",
  successTitle: "Решение отправлено",
  successDesc: "Удачи! Вы можете редактировать заявку до дедлайна.",
  editSubmission: "Редактировать заявку",
  viewProfile: "Смотреть профиль",
  githubRequired: "Ссылка на GitHub обязательна.",
  githubInvalid: "Должна быть корректная ссылка на github.com.",
  liveRequired: "Ссылка на демо обязательна.",
} as const;

export const profile = {
  joinedVia: "Присоединился(ась) через Telegram",
  submissionsLabel: "Заявки",
  winsLabel: "Победы",
  mySubmissions: "Мои заявки",
  theirSubmissions: "Заявки",
  emptyTitle: "Пока нет заявок",
  emptyDesc: "Присоединитесь к активному контесту и отправьте проект, чтобы увидеть его здесь.",
  browseContests: "Смотреть контесты",
} as const;

export const admin = {
  title: "Админ-панель",
  subtitle: "Управляйте контестами, заявками и пользователями.",
  createContest: "Создать контест",
  totalUsers: "Всего пользователей",
  activeContests: "Активные контесты",
  submissionsWord: "Заявки",
  pendingReview: "Ожидают проверки",
  contestsTitle: "Контесты",
  noContestsTitle: "Пока нет контестов",
  noContestsDesc: "Создайте первый контест, чтобы начать.",
  participantsWord: "участников",
  prizeWord: "приз",
  edit: "Изменить",
  recentSubmissions: "Недавние заявки",
  review: "Проверить",
  dashboard: "Панель",
} as const;

export const createContest = {
  heading: "Создать контест",
  editHeading: "Изменить контест",
  titleLabel: "Название контеста",
  titlePlaceholder: "напр. Создайте инструмент для разработчиков на базе ИИ",
  descriptionLabel: "Описание",
  descriptionPlaceholder: "Что должны создать участники?",
  requirementsLabel: "Требования",
  addRequirement: "+ Добавить требование",
  prizeLabel: "Призовой фонд",
  currencyLabel: "Валюта",
  paidLabel: "Платное участие",
  paidHint: "Участник сможет отправить решение только после принятого взноса.",
  entryFeeLabel: "Взнос за участие",
  deadlineLabel: "Дедлайн",
  publishing: "Публикация контеста…",
  publishedMsg: "Контест успешно опубликован.",
  savedMsg: "Черновик сохранён.",
  saveDraft: "Сохранить как черновик",
  publish: "Опубликовать контест",
  livePreview: "Живой предпросмотр",
  live: "Идёт",
  prizeWord: "Приз",
  titleRequired: "Название контеста обязательно.",
  defaultTitle: "Название вашего контеста",
  defaultDesc: "Описание контеста появится здесь по мере ввода.",
} as const;

export const payments = {
  title: "Взносы",
  pending: "На проверке",
  empty: "Взносов пока нет",
  accept: "Принять",
  reject: "Отклонить",
  reasonPlaceholder: "Почему чек отклонён? Участник это увидит.",
  openReceipt: "Открыть чек",
  noReceipt: "Чек ещё не прислан",
  receiptInTelegram: "Чек в Telegram",
  accepted: "Принят",
  rejected: "Отклонён",
  awaiting: "Ждём чек",
  saving: "Сохраняем…",
  close: "Отмена",
  requisitesTitle: "Реквизиты для оплаты",
  requisitesHint:
    "Их видит каждый участник платного контеста. Переносы строк сохраняются.",
  requisitesPlaceholder:
    "Карта: 0000 0000 0000 0000\nПолучатель: имя\nКомментарий: ваш @username",
  requisitesSave: "Сохранить",
  requisitesSaved: "Сохранено",
  requisitesFailed: "Не удалось сохранить. Попробуйте ещё раз.",
} as const;

export const screening = {
  title: "Автопроверка",
  clean: "Проблем не найдено",
  notRun: "Проверка ещё не выполнялась",
  failed: "Проверку выполнить не удалось",
  recheck: "Проверить заново",
  checking: "Проверяем репозиторий…",
  filesScanned: "файлов проверено",
  liveOk: "Демо отвечает",
  liveBad: "Демо отвечает ошибкой",
  liveDead: "Демо не отвечает",
  stars: "звёзд",
  sizeKb: "КБ",
  severityHigh: "важно",
  severityMedium: "стоит взглянуть",
  hint: "Находки ничего не блокируют — решение остаётся за вами.",
} as const;

export const review = {
  deleteCta: "Удалить заявку",
  deleteConfirm: "Удалить заявку без возможности вернуть?",
  deleting: "Удаляем…",
  deleteFailed: "Не удалось удалить. Попробуйте ещё раз.",
  notFoundTitle: "Заявка не найдена",
  notFoundDesc: "Возможно, она была отозвана участником.",
  backToDashboard: "Назад к панели",
  dashboard: "Панель",
  demoVideo: "Демо-видео",
  description: "Описание",
  scoreLabel: "Оценка (0–100)",
  notesLabel: "Заметки проверяющего",
  notesPlaceholder: "Внутренние заметки (не видны участнику)",
  markWinner: "Отметить как победителя",
  saving: "Сохранение проверки…",
  saved: "Проверка сохранена.",
  saveReview: "Сохранить проверку",
  openRepo: "Открыть репозиторий",
  openDemo: "Открыть демонстрацию",
} as const;

/** Бейджи статусов — те же четыре, что и в макетах. */
export const statusLabels = {
  draft: "Черновик",
  submitted: "Отправлено",
  reviewed: "Проверено",
  winner: "Победитель",
  live: "Идёт",
  ended: "Завершён",
  archived: "В архиве",
} as const;

export const common = {
  loading: "Загрузка…",
  error: "Что-то пошло не так",
  errorDesc: "Попробуйте обновить страницу.",
  retry: "Попробовать снова",
  back: "Назад",
} as const;

export const analytics = {
  title: "Аналитика",
  subtitle: "Посещаемость сайта и действия посетителей",
  views: "Просмотры",
  visitors: "Уникальные посетители",
  loggedIn: "Из них вошли",
  clicksTotal: "Действий",
  perDay: "По дням",
  pages: "Страницы",
  events: "Действия",
  pageColumn: "Страница",
  actionColumn: "Действие",
  viewsColumn: "Просмотры",
  visitorsColumn: "Посетители",
  countColumn: "Всего",
  empty: "Данных пока нет. Они появятся, как только на сайт зайдут.",
  noEvents: "Кнопки пока никто не нажимал.",
  days7: "7 дней",
  days30: "30 дней",
  days90: "90 дней",
  visitorsHint: "Посетители считаются анонимно: IP-адреса не сохраняются.",
} as const;

/** Понятные названия событий. Незнакомое покажем как есть. */
export const eventLabels: Record<string, string> = {
  participate_click: "Нажали «Участвовать»",
};
