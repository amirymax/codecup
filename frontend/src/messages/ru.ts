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
  prizeLabel: "Призовой фонд (USD)",
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

export const review = {
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
