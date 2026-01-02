/**
 * CodeProof - Internationalization (i18n) System
 *
 * Bilingual support for English and Spanish.
 *
 * Usage:
 *   t('login') // Returns "Login" or "Iniciar Sesión"
 *   switchLanguage('es') // Switch to Spanish
 *   getCurrentLanguage() // Returns current language code
 *
 * HTML Usage:
 *   <h1 data-i18n="welcome.title">Welcome</h1>
 *   Will be automatically translated when language changes
 */

// Current language (default: English)
let currentLanguage = 'en';

// Translation dictionary
const translations = {
  en: {
    // Common
    'common.loading': 'Loading...',
    'common.submit': 'Submit',
    'common.cancel': 'Cancel',
    'common.save': 'Save',
    'common.delete': 'Delete',
    'common.edit': 'Edit',
    'common.close': 'Close',
    'common.back': 'Back',
    'common.next': 'Next',
    'common.search': 'Search',
    'common.filter': 'Filter',
    'common.reset': 'Reset',
    'common.confirm': 'Confirm',
    'common.yes': 'Yes',
    'common.no': 'No',
    'common.view': 'View',
    'common.copy': 'Copy',
    'common.viewAll': 'View All',
    'common.solved': 'Solved',
    'common.unsolved': 'Unsolved',

    // Auth
    'auth.login': 'Login',
    'auth.logout': 'Logout',
    'auth.register': 'Register',
    'auth.username': 'Username',
    'auth.password': 'Password',
    'auth.confirmPassword': 'Confirm Password',
    'auth.rememberMe': 'Remember me',
    'auth.forgotPassword': 'Forgot password?',
    'auth.noAccount': "Don't have an account?",
    'auth.hasAccount': 'Already have an account?',
    'auth.signUp': 'Sign up',
    'auth.signIn': 'Sign in',
    'auth.confirmLogout': 'Are you sure you want to logout?',
    'auth.logoutSuccess': 'Logged out successfully',
    'auth.subtitle': 'Bitcoin Online Judge Platform',
    'auth.tabs.login': 'Login',
    'auth.tabs.register': 'Register',
    'auth.fields.username': 'Username',
    'auth.fields.password': 'Password',
    'auth.fields.confirmPassword': 'Confirm Password',
    'auth.placeholders.username': 'Enter your username',
    'auth.placeholders.password': 'Enter your password',
    'auth.placeholders.confirmPassword': 'Confirm your password',
    'auth.placeholders.chooseUsername': 'Choose a username',
    'auth.placeholders.choosePassword': 'Choose a password',
    'auth.buttons.login': 'Login',
    'auth.buttons.register': 'Register',
    'auth.demo.title': 'Demo Users (for testing):',
    'auth.help.usernameMin': 'Minimum 3 characters',
    'auth.help.passwordMin': 'Minimum 6 characters',
    'auth.messages.loginSuccess': 'Welcome back, {username}!',
    'auth.messages.loginError': 'Invalid username or password',
    'auth.messages.registerSuccess': 'Welcome, {username}!',
    'auth.messages.registerError': 'Registration failed. Username may already exist.',
    'auth.messages.passwordMismatch': 'Passwords do not match',

    // Navigation
    'nav.dashboard': 'Dashboard',
    'nav.problems': 'Problems',
    'nav.submissions': 'Submissions',
    'nav.ranking': 'Ranking',
    'nav.blockchain': 'Blockchain',
    'nav.admin': 'Admin',
    'nav.problemsetter': 'Problemsetter',
    'nav.profile': 'Profile',
    'nav.settings': 'Settings',
    'nav.blocks': 'Blockchain',
    'nav.role': 'Role',
    'nav.howItWorks': 'How It Works',
    'nav.login': 'Login',
    'nav.logout': 'Logout',
    'nav.register': 'Register',

    // Roles
    'roles.admin': 'Admin',
    'roles.problemsetter': 'Problemsetter',
    'roles.user': 'User',

    // Dashboard
    'dashboard.welcome': 'Welcome',
    'dashboard.subtitle': 'Track your progress, solve problems, and climb the leaderboard',
    'dashboard.totalScore': 'Total Score',
    'dashboard.problemsSolved': 'Problems Solved',
    'dashboard.rank': 'Global Rank',
    'dashboard.submissions': 'Submissions',
    'dashboard.accuracy': 'Accuracy',
    'dashboard.recentActivity': 'Recent Activity',
    'dashboard.quickLinks': 'Quick Links',
    'dashboard.recentBlocks': 'Recent Blocks',
    'dashboard.noActivity': 'No recent activity. Start solving problems!',
    'dashboard.cta.title': 'Ready to solve more problems?',
    'dashboard.cta.description': 'Challenge yourself with Bitcoin-themed coding problems and earn points',
    'dashboard.cta.button': 'Browse Problems →',

    // Quick Links
    'quickLinks.problems.title': 'Solve Problems',
    'quickLinks.problems.desc': 'Browse and solve coding challenges',
    'quickLinks.submissions.title': 'Submissions',
    'quickLinks.submissions.desc': 'View your submission history',
    'quickLinks.ranking.title': 'Leaderboard',
    'quickLinks.ranking.desc': 'See how you rank globally',
    'quickLinks.blocks.title': 'Blockchain',
    'quickLinks.blocks.desc': 'Explore mined blocks',

    // Settings
    'settings.title': 'Account Settings',
    'settings.subtitle': 'Manage your account information and preferences',
    'settings.profileInfo': 'Profile Information',
    'settings.profileInfoDesc': 'Update your profile details and contact information',
    'settings.username': 'Username',
    'settings.usernameHelp': 'Username cannot be changed',
    'settings.email': 'Email',
    'settings.emailHelp': 'Your email address for notifications and account recovery',
    'settings.npub': 'Nostr Public Key (npub)',
    'settings.npubHelp': 'Your Nostr public key for decentralized identity',
    'settings.github': 'GitHub Profile',
    'settings.githubHelp': 'Link to your GitHub profile',
    'settings.country': 'Country',
    'settings.countryHelp': 'Your country of residence',
    'settings.organization': 'Organization',
    'settings.organizationHelp': 'Your school, university, or company',
    'settings.saveProfile': 'Save Profile',
    'settings.saving': 'Saving...',
    'settings.changePassword': 'Change Password',
    'settings.changePasswordDesc': 'Update your password to keep your account secure',
    'settings.currentPassword': 'Current Password',
    'settings.newPassword': 'New Password',
    'settings.passwordHelp': 'Minimum 8 characters',
    'settings.confirmPassword': 'Confirm New Password',
    'settings.updatePassword': 'Update Password',
    'settings.profileUpdated': 'Profile updated successfully!',
    'settings.profileUpdateError': 'Failed to update profile',
    'settings.passwordChanged': 'Password changed successfully',
    'settings.passwordChangeError': 'Failed to change password',

    // Profile
    'profile.title': 'Profile',
    'profile.memberSince': 'Member since',
    'profile.edit': 'Edit Profile',
    'profile.solved': 'Solved',
    'profile.rank': 'Rank',
    'profile.score': 'Score',
    'profile.acceptance': 'Acceptance',
    'profile.streak': 'Streak',
    'profile.sats': 'Sats',
    'profile.recentActivity': 'Recent Activity',
    'profile.noActivity': 'No recent activity',
    'profile.solvedProblems': 'Solved Problems',
    'profile.noProblemsSolved': 'No problems solved yet',
    'profile.attemptedProblems': 'Attempted Problems',
    'profile.noProblemsAttempted': 'No problems attempted yet',
    'profile.blockchain': 'Blockchain Activity',
    'profile.onChain': 'On-Chain Submissions',
    'profile.blocks': 'Blocks Mined',
    'profile.lastBlock': 'Last Block',
    'profile.languages': 'Languages Used',
    'profile.submissions': 'Submission Stats',
    'profile.notFound.title': 'User Not Found',
    'profile.notFound.message': 'The user <strong>{username}</strong> doesn\'t exist or hasn\'t registered yet.',
    'profile.notFound.viewLeaderboard': 'View Leaderboard',
    'profile.notFound.goToDashboard': 'Go to Dashboard',

    // Blocks
    'blocks.nextBlock': 'Next block in',
    'blocks.title': 'Blockchain Explorer',
    'blocks.subtitle': 'CodeProof blocks mined every 10 minutes, containing all accepted submissions',
    'blocks.stats.latestBlock': 'Latest Block',
    'blocks.stats.totalBlocks': 'Total Blocks',
    'blocks.stats.totalTx': 'Total Transactions',
    'blocks.stats.nextBlock': 'Next Block In',
    'blocks.mempool.title': 'Mempool',
    'blocks.mempool.waiting': '{count} transactions waiting',
    'blocks.mempool.empty': 'No pending transactions',
    'blocks.timeline.title': 'Recent Blocks',
    'blocks.timeline.refresh': 'Refresh',
    'blocks.timeline.legend': 'Legend:',

    // Problems
    'problems.title': 'Problems',
    'problems.subtitle': 'Solve Bitcoin-themed coding challenges and earn points',
    'problems.available': 'Available Problems',
    'problems.difficulty': 'Difficulty',
    'problems.points': 'Points',
    'problems.solved': 'Solved',
    'problems.unsolved': 'Unsolved',
    'problems.solvedCount': '{count} solved',
    'problems.filterByDifficulty': 'Filter by difficulty',
    'problems.searchPlaceholder': 'Search problems...',
    'problems.noProblem': 'No problems found',
    'problems.table.title': 'Title',
    'problems.table.difficulty': 'Difficulty',
    'problems.table.points': 'Points',
    'problems.table.solved': 'Solved',
    'problems.table.status': 'Status',
    'problems.difficulty.easy': 'Easy',
    'problems.difficulty.medium': 'Medium',
    'problems.difficulty.hard': 'Hard',
    'problems.empty.title': 'No problems yet',
    'problems.empty.description': 'Check back soon for new challenges',
    'problems.filters.search': 'Search by title',
    'problems.filters.difficulty': 'Difficulty',
    'problems.filters.status': 'Status',
    'problems.filters.all': 'All',
    'problems.filters.solved': 'Solved',
    'problems.filters.unsolved': 'Unsolved',
    'problems.filters.showing': 'Showing',
    'problems.filters.of': 'of',
    'problems.filters.problems': 'problems',
    'problems.filters.noResults': 'No problems match your filters',

    // Difficulty levels
    'difficulty.easy': 'Easy',
    'difficulty.medium': 'Medium',
    'difficulty.hard': 'Hard',
    'difficulty.all': 'All Difficulties',

    // Problem detail
    'problem.backToProblems': 'Back to Problems',
    'problem.description': 'Description',
    'problem.inputFormat': 'Input Format',
    'problem.outputFormat': 'Output Format',
    'problem.sampleTests': 'Sample Test Cases',
    'problem.sample': 'Sample',
    'problem.input': 'Input',
    'problem.output': 'Expected Output',
    'problem.constraints': 'Constraints',
    'problem.timeLimit': 'Time Limit',
    'problem.memoryLimit': 'Memory Limit',
    'problem.currentPoints': 'Current Points',
    'problem.solvedBy': 'Solved By',
    'problem.accuracy': 'Accuracy',
    'problem.points': 'points',
    'problem.yourSolution': 'Your Solution',
    'problem.yourCode': 'Your Code',
    'problem.language': 'Language',
    'problem.autoSave': 'Auto-save enabled',
    'problem.toggleTheme': 'Theme',
    'problem.submitCode': 'Submit Code',
    'problem.resetCode': 'Reset to Template',
    'problem.viewEditorial': 'View Editorial',
    'problem.editorial': 'Editorial',
    'problem.close': 'Close',
    'problem.submit': 'Submit Code',
    'problem.reset': 'Reset Code',
    'problem.theme': 'Editor Theme',
    'problem.themeDark': 'Dark',
    'problem.themeLight': 'Light',
    'problem.submitting': 'Submitting...',
    'problem.submissionReceived': 'Submission received! Judging...',
    'problem.recentSubmissions': 'Your Recent Submissions',
    'problem.noSubmissions': 'No submissions yet. Submit your solution to get started!',

    // Submissions
    'submissions.title': 'Submissions',
    'submissions.description': 'View all your code submissions and their results',
    'submissions.id': 'ID',
    'submissions.user': 'User',
    'submissions.problem': 'Problem',
    'submissions.language': 'Language',
    'submissions.verdict': 'Verdict',
    'submissions.time': 'Time',
    'submissions.memory': 'Memory',
    'submissions.submittedAt': 'Submitted At',
    'submissions.viewCode': 'View Code',
    'submissions.testResults': 'Test Results',
    'submissions.noSubmissions': 'No submissions yet',
    'submissions.noSubmissionsText': 'Start solving problems to see your submissions here',
    'submissions.browsePproblems': 'Browse Problems',
    'submissions.filterByVerdict': 'Filter by Verdict',
    'submissions.filterByProblem': 'Filter by Problem',
    'submissions.allVerdicts': 'All Verdicts',
    'submissions.allProblems': 'All Problems',
    'submissions.totalSubmissions': 'Total Submissions',
    'submissions.accepted': 'Accepted',
    'submissions.acceptanceRate': 'Acceptance Rate',
    'submissions.submissionDetails': 'Submission Details',
    'submissions.submissionId': 'Submission ID',
    'submissions.sourceCode': 'Source Code',

    // Verdicts
    'verdict.AC': 'Accepted',
    'verdict.WA': 'Wrong Answer',
    'verdict.TLE': 'Time Limit Exceeded',
    'verdict.MLE': 'Memory Limit Exceeded',
    'verdict.RE': 'Runtime Error',
    'verdict.CE': 'Compilation Error',
    'verdict.PENDING': 'Pending',
    'verdicts.AC': 'Accepted',
    'verdicts.WA': 'Wrong Answer',
    'verdicts.TLE': 'Time Limit Exceeded',
    'verdicts.MLE': 'Memory Limit Exceeded',
    'verdicts.RE': 'Runtime Error',

    // Ranking
    'ranking.title': 'Leaderboard',
    'ranking.description': 'Top players ranked by total score',
    'ranking.rank': 'Rank',
    'ranking.username': 'Username',
    'ranking.totalScore': 'Total Score',
    'ranking.problemsSolved': 'Problems Solved',
    'ranking.you': 'You',
    'ranking.totalUsers': 'Total Users',
    'ranking.yourRank': 'Your Rank',
    'ranking.yourScore': 'Your Score',

    // Admin
    'admin.title': 'Admin Panel - CodeProof',
    'admin.pageTitle': 'Admin Panel',
    'admin.subtitle': 'Manage users, problems, and system settings',
    'admin.tabs.users': 'Users',
    'admin.tabs.problems': 'Problems',
    'admin.tabs.stats': 'Statistics',

    // Admin - Users Tab
    'admin.users.title': 'User Management',
    'admin.users.subtitle': 'Manage user roles and permissions',
    'admin.users.search': 'Search Users',
    'admin.users.searchPlaceholder': 'Search by username or email...',
    'admin.users.filterRole': 'Filter by Role',
    'admin.users.allRoles': 'All Roles',
    'admin.users.results': 'Results',
    'admin.users.usersFound': 'users found',
    'admin.users.empty': 'No users found',
    'admin.users.table.id': 'ID',
    'admin.users.table.username': 'Username',
    'admin.users.table.email': 'Email',
    'admin.users.table.role': 'Role',
    'admin.users.table.score': 'Total Score',
    'admin.users.table.solved': 'Problems Solved',
    'admin.users.table.createdAt': 'Created At',
    'admin.users.table.actions': 'Actions',
    'admin.users.resetPassword': 'Reset Password',

    // Admin - Problems Tab
    'admin.problems.title': 'Problem Management',
    'admin.problems.subtitle': 'Review and approve pending problems',
    'admin.problems.empty': 'No pending problems',
    'admin.problems.emptyDesc': 'All problems have been reviewed',
    'admin.problems.table.id': 'ID',
    'admin.problems.table.title': 'Title',
    'admin.problems.table.difficulty': 'Difficulty',
    'admin.problems.table.createdBy': 'Created By',
    'admin.problems.table.createdAt': 'Created At',
    'admin.problems.table.status': 'Status',
    'admin.problems.table.actions': 'Actions',
    'admin.problems.approve': 'Approve',
    'admin.problems.reject': 'Reject',
    'admin.problems.detail.difficulty': 'Difficulty',
    'admin.problems.detail.creator': 'Created by',
    'admin.problems.detail.description': 'Description Preview',

    // Admin - Stats Tab
    'admin.stats.title': 'System Statistics',
    'admin.stats.totalUsers': 'Total Users',
    'admin.stats.totalProblems': 'Total Problems',
    'admin.stats.totalSubmissions': 'Total Submissions',
    'admin.stats.pendingProblems': 'Pending Problems',
    'admin.stats.acSubmissions': 'AC Submissions',
    'admin.stats.acceptanceRate': 'Acceptance Rate',
    'admin.stats.recentActivity': 'Recent Activity',
    'admin.stats.activeToday': 'Active users today',
    'admin.stats.submissionsToday': 'Submissions today',
    'admin.stats.newUsersWeek': 'New users this week',
    'admin.stats.systemHealth': 'System Health',

    // Admin - Password Reset Modal
    'admin.passwordReset.title': 'Reset User Password',
    'admin.passwordReset.description': 'Enter a new password for this user. Make sure to communicate it securely.',
    'admin.passwordReset.username': 'Username',
    'admin.passwordReset.newPassword': 'New Password',
    'admin.passwordReset.confirmPassword': 'Confirm Password',
    'admin.passwordReset.passwordHelp': 'Minimum 8 characters',
    'admin.passwordReset.setPassword': 'Set Password',
    'admin.passwordReset.warning': '⚠️ Warning:',
    'admin.passwordReset.warningText': 'Make sure to communicate this password securely to the user.',

    // Problemsetter
    'problemsetter.title': 'Problemsetter Panel - CodeProof',
    'problemsetter.pageTitle': 'Problemsetter Panel',
    'problemsetter.subtitle': 'Create and manage coding problems for the platform',
    'problemsetter.tabs.create': 'Create Problem',
    'problemsetter.tabs.myProblems': 'My Problems',
    'problemsetter.tabs.submissions': 'Submissions',

    // Problemsetter - Create Tab
    'problemsetter.create.title': 'Create New Problem',
    'problemsetter.create.subtitle': 'Fill in the details below to submit a new problem for review',
    'problemsetter.create.submit': 'Submit Problem for Review',

    // Problemsetter - My Problems Tab
    'problemsetter.myProblems.title': 'My Problems',
    'problemsetter.myProblems.subtitle': 'Track the status of your submitted problems',
    'problemsetter.myProblems.filterStatus': 'Filter by Status',
    'problemsetter.myProblems.allStatuses': 'All Statuses',
    'problemsetter.myProblems.pending': 'Pending',
    'problemsetter.myProblems.approved': 'Approved',
    'problemsetter.myProblems.rejected': 'Rejected',
    'problemsetter.myProblems.empty': 'No problems found',
    'problemsetter.myProblems.emptyDesc': 'Create your first problem to get started!',
    'problemsetter.myProblems.table.id': 'ID',
    'problemsetter.myProblems.table.title': 'Title',
    'problemsetter.myProblems.table.difficulty': 'Difficulty',
    'problemsetter.myProblems.table.status': 'Status',
    'problemsetter.myProblems.table.createdAt': 'Created At',
    'problemsetter.myProblems.table.actions': 'Actions',

    // Problemsetter - Submissions Tab
    'problemsetter.submissions.title': 'Submissions to My Problems',
    'problemsetter.submissions.subtitle': 'View all submissions to your approved problems',
    'problemsetter.submissions.empty': 'No submissions yet',
    'problemsetter.submissions.emptyDesc': 'Once your problems are approved, submissions will appear here',
    'problemsetter.submissions.table.user': 'User',

    // Create Problem
    'createProblem.title': 'Create Problem',
    'createProblem.titleEN': 'Title (English)',
    'createProblem.titleES': 'Title (Spanish)',
    'createProblem.titleENPlaceholder': 'e.g., Hello Bitcoin',
    'createProblem.titleESPlaceholder': 'e.g., Hola Bitcoin',
    'createProblem.descriptionEN': 'Description (English)',
    'createProblem.descriptionES': 'Description (Spanish)',
    'createProblem.descriptionENPlaceholder': 'Write problem description in markdown...',
    'createProblem.descriptionESPlaceholder': 'Escribe la descripción del problema en markdown...',
    'createProblem.difficulty': 'Difficulty',
    'createProblem.timeLimit': 'Time Limit (seconds)',
    'createProblem.memoryLimit': 'Memory Limit (MB)',
    'createProblem.sampleTests': 'Sample Test Cases (visible to users)',
    'createProblem.hiddenTests': 'Hidden Test Cases (for judging only)',
    'createProblem.addTest': 'Add Test',
    'createProblem.input': 'Input',
    'createProblem.expectedOutput': 'Expected Output',
    'createProblem.preview': 'Preview',
    'createProblem.togglePreview': 'Toggle Preview',

    // Notifications
    'notif.loginSuccess': 'Login successful',
    'notif.loginError': 'Invalid credentials',
    'notif.logoutSuccess': 'Logged out successfully',
    'notif.submitSuccess': 'Code submitted successfully',
    'notif.submitError': 'Failed to submit code',
    'notif.saveSuccess': 'Saved successfully',
    'notif.saveError': 'Failed to save',
    'notif.deleteSuccess': 'Deleted successfully',
    'notif.deleteError': 'Failed to delete',

    // Errors
    'error.generic': 'An error occurred',
    'error.network': 'Network error. Please check your connection.',
    'error.unauthorized': 'You are not authorized to perform this action',
    'error.notFound': 'Resource not found',
    'error.validation': 'Please check your input',
    'errors.unauthorized': 'You do not have permission to access this page',
    'errors.problemNotFound': 'Problem not found',
    'errors.loadProblemFailed': 'Failed to load problem',
    'errors.codeEmpty': 'Code cannot be empty',
    'errors.submissionFailed': 'Failed to submit code',
    'errors.judgingTimeout': 'Judging is taking longer than expected. Check submissions page.',

    // Time units
    'time.seconds': '{count}s',
    'time.milliseconds': '{count}ms',
    'time.minutes': '{count}m',
    'time.hours': '{count}h',
    'time.days': '{count}d',
    'time.justNow': 'Just now',
    'time.ago': '{time} ago',

    // Landing Page - Hero
    'hero.title': 'Prove Your Code on the Bitcoin Ecosystem',
    'hero.subtitle': 'Solve Bitcoin-themed coding challenges and compete globally',
    'hero.cta.start': 'Start Solving',
    'hero.cta.browse': 'Browse Problems',
    'hero.stats.submissions': 'Submissions',
    'hero.stats.users': 'Users',
    'hero.stats.blocks': 'Blocks Mined',
    'hero.stats.problems': 'Problems',

    // Landing Page - Features
    'features.title': 'Why CodeProof?',
    'features.dynamic.title': 'Dynamic Scoring',
    'features.dynamic.desc': 'Problem points decrease as more users solve them, rewarding early solvers',
    'features.learn.title': 'Learn Bitcoin',
    'features.learn.desc': 'Master Bitcoin concepts through hands-on coding challenges',
    'features.compete.title': 'Compete Globally',
    'features.compete.desc': 'Climb the leaderboard and prove your skills against developers worldwide',

    // Landing Page - How It Works
    'howItWorks.title': 'How It Works',
    'howItWorks.step1.title': 'Choose a Problem',
    'howItWorks.step1.desc': 'Explore Bitcoin coding challenges',
    'howItWorks.step2.title': 'Code and Test',
    'howItWorks.step2.desc': 'Write and test your solution against sample cases',
    'howItWorks.step3.title': 'Submit Your Code',
    'howItWorks.step3.desc': 'Real-time automatic evaluation',
    'howItWorks.step4.title': 'Earn Points & Climb the Ranking',
    'howItWorks.step4.desc': 'Your accepted solution earns points and others can see it',
    'howItWorks.step5.title': 'Recorded in Blocks Every 10 Min',
    'howItWorks.step5.desc': 'Solutions are recorded in blocks. The first user to solve each problem becomes the block\'s "miner"',

    // Landing Page - Leaderboard
    'leaderboard.title': 'Top Players',
    'leaderboard.viewAll': 'Full Ranking →',

    // Landing Page - Footer
    'footer.platform': 'Platform',
    'footer.problems': 'Problems',
    'footer.blocks': 'Blockchain',
    'footer.ranking': 'Ranking',
    'footer.login': 'Login',
    'footer.resources': 'Resources',
    'footer.docs': 'Documentation',
    'footer.api': 'API',
    'footer.github': 'GitHub',
    'footer.howItWorks': 'How It Works',
    'footer.legal': 'Legal',
    'footer.about': 'About',
    'footer.contact': 'Contact',
    'footer.terms': 'Terms of Service',
    'footer.privacy': 'Privacy Policy',
  },

  es: {
    // Common
    'common.loading': 'Cargando...',
    'common.submit': 'Enviar',
    'common.cancel': 'Cancelar',
    'common.save': 'Guardar',
    'common.delete': 'Eliminar',
    'common.edit': 'Editar',
    'common.close': 'Cerrar',
    'common.back': 'Volver',
    'common.next': 'Siguiente',
    'common.search': 'Buscar',
    'common.filter': 'Filtrar',
    'common.reset': 'Reiniciar',
    'common.confirm': 'Confirmar',
    'common.yes': 'Sí',
    'common.no': 'No',
    'common.view': 'Ver',
    'common.copy': 'Copiar',
    'common.viewAll': 'Ver Todos',
    'common.solved': 'Resuelto',
    'common.unsolved': 'Sin Resolver',

    // Auth
    'auth.login': 'Iniciar Sesión',
    'auth.logout': 'Cerrar Sesión',
    'auth.register': 'Registrarse',
    'auth.username': 'Usuario',
    'auth.password': 'Contraseña',
    'auth.confirmPassword': 'Confirmar Contraseña',
    'auth.rememberMe': 'Recordarme',
    'auth.forgotPassword': '¿Olvidaste tu contraseña?',
    'auth.noAccount': '¿No tienes cuenta?',
    'auth.hasAccount': '¿Ya tienes cuenta?',
    'auth.signUp': 'Regístrate',
    'auth.signIn': 'Inicia sesión',
    'auth.confirmLogout': '¿Estás seguro de que deseas cerrar sesión?',
    'auth.logoutSuccess': 'Sesión cerrada exitosamente',
    'auth.subtitle': 'Plataforma de Juez en Línea de Bitcoin',
    'auth.tabs.login': 'Iniciar Sesión',
    'auth.tabs.register': 'Registrarse',
    'auth.fields.username': 'Usuario',
    'auth.fields.password': 'Contraseña',
    'auth.fields.confirmPassword': 'Confirmar Contraseña',
    'auth.placeholders.username': 'Ingresa tu usuario',
    'auth.placeholders.password': 'Ingresa tu contraseña',
    'auth.placeholders.confirmPassword': 'Confirma tu contraseña',
    'auth.placeholders.chooseUsername': 'Elige un usuario',
    'auth.placeholders.choosePassword': 'Elige una contraseña',
    'auth.buttons.login': 'Iniciar Sesión',
    'auth.buttons.register': 'Registrarse',
    'auth.demo.title': 'Usuarios de Prueba (para testing):',
    'auth.help.usernameMin': 'Mínimo 3 caracteres',
    'auth.help.passwordMin': 'Mínimo 6 caracteres',
    'auth.messages.loginSuccess': '¡Bienvenido de nuevo, {username}!',
    'auth.messages.loginError': 'Usuario o contraseña inválidos',
    'auth.messages.registerSuccess': '¡Bienvenido, {username}!',
    'auth.messages.registerError': 'Registro fallido. El usuario puede ya existir.',
    'auth.messages.passwordMismatch': 'Las contraseñas no coinciden',

    // Navigation
    'nav.dashboard': 'Inicio',
    'nav.problems': 'Problemas',
    'nav.submissions': 'Envíos',
    'nav.ranking': 'Ranking',
    'nav.blockchain': 'Blockchain',
    'nav.admin': 'Administración',
    'nav.problemsetter': 'Crear Problemas',
    'nav.profile': 'Perfil',
    'nav.settings': 'Configuración',
    'nav.blocks': 'Blockchain',
    'nav.role': 'Rol',
    'nav.howItWorks': 'Cómo Funciona',
    'nav.login': 'Iniciar Sesión',
    'nav.logout': 'Cerrar Sesión',
    'nav.register': 'Registrarse',

    // Roles
    'roles.admin': 'Administrador',
    'roles.problemsetter': 'Creador de Problemas',
    'roles.user': 'Usuario',

    // Dashboard
    'dashboard.welcome': 'Bienvenido',
    'dashboard.subtitle': 'Rastrea tu progreso, resuelve problemas y sube en el ranking',
    'dashboard.totalScore': 'Puntos Totales',
    'dashboard.problemsSolved': 'Problemas Resueltos',
    'dashboard.rank': 'Ranking Global',
    'dashboard.submissions': 'Envíos',
    'dashboard.accuracy': 'Precisión',
    'dashboard.recentActivity': 'Actividad Reciente',
    'dashboard.quickLinks': 'Accesos Rápidos',
    'dashboard.recentBlocks': 'Bloques Recientes',
    'dashboard.noActivity': 'Sin actividad reciente. ¡Comienza a resolver problemas!',
    'dashboard.cta.title': '¿Listo para resolver más problemas?',
    'dashboard.cta.description': 'Desafíate con problemas de código temáticos de Bitcoin y gana puntos',
    'dashboard.cta.button': 'Ver Problemas →',

    // Quick Links
    'quickLinks.problems.title': 'Resolver Problemas',
    'quickLinks.problems.desc': 'Explora y resuelve desafíos de código',
    'quickLinks.submissions.title': 'Envíos',
    'quickLinks.submissions.desc': 'Ve tu historial de envíos',
    'quickLinks.ranking.title': 'Clasificación',
    'quickLinks.ranking.desc': 'Ve tu posición global',
    'quickLinks.blocks.title': 'Blockchain',
    'quickLinks.blocks.desc': 'Explora bloques minados',

    // Settings
    'settings.title': 'Configuración de Cuenta',
    'settings.subtitle': 'Administra la información de tu cuenta y preferencias',
    'settings.profileInfo': 'Información del Perfil',
    'settings.profileInfoDesc': 'Actualiza los detalles de tu perfil e información de contacto',
    'settings.username': 'Usuario',
    'settings.usernameHelp': 'El nombre de usuario no se puede cambiar',
    'settings.email': 'Correo Electrónico',
    'settings.emailHelp': 'Tu dirección de correo para notificaciones y recuperación de cuenta',
    'settings.npub': 'Clave Pública Nostr (npub)',
    'settings.npubHelp': 'Tu clave pública de Nostr para identidad descentralizada',
    'settings.github': 'Perfil de GitHub',
    'settings.githubHelp': 'Enlace a tu perfil de GitHub',
    'settings.country': 'País',
    'settings.countryHelp': 'Tu país de residencia',
    'settings.organization': 'Organización',
    'settings.organizationHelp': 'Tu escuela, universidad o empresa',
    'settings.saveProfile': 'Guardar Perfil',
    'settings.saving': 'Guardando...',
    'settings.changePassword': 'Cambiar Contraseña',
    'settings.changePasswordDesc': 'Actualiza tu contraseña para mantener tu cuenta segura',
    'settings.currentPassword': 'Contraseña Actual',
    'settings.newPassword': 'Nueva Contraseña',
    'settings.passwordHelp': 'Mínimo 8 caracteres',
    'settings.confirmPassword': 'Confirmar Nueva Contraseña',
    'settings.updatePassword': 'Actualizar Contraseña',
    'settings.profileUpdated': '¡Perfil actualizado correctamente!',
    'settings.profileUpdateError': 'Error al actualizar el perfil',
    'settings.passwordChanged': 'Contraseña cambiada correctamente',
    'settings.passwordChangeError': 'Error al cambiar la contraseña',

    // Profile
    'profile.title': 'Perfil',
    'profile.memberSince': 'Miembro desde',
    'profile.edit': 'Editar Perfil',
    'profile.solved': 'Resueltos',
    'profile.rank': 'Posición',
    'profile.score': 'Puntuación',
    'profile.acceptance': 'Aceptación',
    'profile.streak': 'Racha',
    'profile.sats': 'Sats',
    'profile.recentActivity': 'Actividad Reciente',
    'profile.noActivity': 'No hay actividad reciente',
    'profile.solvedProblems': 'Problemas Resueltos',
    'profile.noProblemsSolved': 'Aún no has resuelto ningún problema',
    'profile.attemptedProblems': 'Problemas Intentados',
    'profile.noProblemsAttempted': 'Aún no has intentado ningún problema',
    'profile.blockchain': 'Actividad Blockchain',
    'profile.onChain': 'Envíos On-Chain',
    'profile.blocks': 'Bloques Minados',
    'profile.lastBlock': 'Último Bloque',
    'profile.languages': 'Lenguajes Usados',
    'profile.submissions': 'Estadísticas de Envíos',
    'profile.notFound.title': 'Usuario No Encontrado',
    'profile.notFound.message': 'El usuario <strong>{username}</strong> no existe o no se ha registrado aún.',
    'profile.notFound.viewLeaderboard': 'Ver Clasificación',
    'profile.notFound.goToDashboard': 'Ir al Dashboard',

    // Blocks
    'blocks.nextBlock': 'Próximo bloque en',
    'blocks.title': 'Explorador de Blockchain',
    'blocks.subtitle': 'Bloques de CodeProof minados cada 10 minutos, conteniendo todas las submissions aceptadas',
    'blocks.stats.latestBlock': 'Último Bloque',
    'blocks.stats.totalBlocks': 'Total de Bloques',
    'blocks.stats.totalTx': 'Total de Transacciones',
    'blocks.stats.nextBlock': 'Próximo Bloque En',
    'blocks.mempool.title': 'Mempool',
    'blocks.mempool.waiting': '{count} transacciones esperando',
    'blocks.mempool.empty': 'No hay transacciones pendientes',
    'blocks.timeline.title': 'Bloques Recientes',
    'blocks.timeline.refresh': 'Actualizar',
    'blocks.timeline.legend': 'Leyenda:',

    // Problems
    'problems.title': 'Problemas',
    'problems.subtitle': 'Resuelve desafíos de código temáticos de Bitcoin y gana puntos',
    'problems.available': 'Problemas Disponibles',
    'problems.difficulty': 'Dificultad',
    'problems.points': 'Puntos',
    'problems.solved': 'Resueltos',
    'problems.unsolved': 'Sin Resolver',
    'problems.solvedCount': '{count} resuelto(s)',
    'problems.filterByDifficulty': 'Filtrar por dificultad',
    'problems.searchPlaceholder': 'Buscar problemas...',
    'problems.noProblem': 'No se encontraron problemas',
    'problems.table.title': 'Título',
    'problems.table.difficulty': 'Dificultad',
    'problems.table.points': 'Puntos',
    'problems.table.solved': 'Resueltos',
    'problems.table.status': 'Estado',
    'problems.difficulty.easy': 'Fácil',
    'problems.difficulty.medium': 'Medio',
    'problems.difficulty.hard': 'Difícil',
    'problems.empty.title': 'Aún no hay problemas',
    'problems.empty.description': 'Vuelve pronto para nuevos desafíos',
    'problems.filters.search': 'Buscar por título',
    'problems.filters.difficulty': 'Dificultad',
    'problems.filters.status': 'Estado',
    'problems.filters.all': 'Todos',
    'problems.filters.solved': 'Resueltos',
    'problems.filters.unsolved': 'Sin Resolver',
    'problems.filters.showing': 'Mostrando',
    'problems.filters.of': 'de',
    'problems.filters.problems': 'problemas',
    'problems.filters.noResults': 'No hay problemas que coincidan con tus filtros',

    // Difficulty levels
    'difficulty.easy': 'Fácil',
    'difficulty.medium': 'Medio',
    'difficulty.hard': 'Difícil',
    'difficulty.all': 'Todas las Dificultades',

    // Problem detail
    'problem.backToProblems': 'Volver a Problemas',
    'problem.description': 'Descripción',
    'problem.inputFormat': 'Formato de Entrada',
    'problem.outputFormat': 'Formato de Salida',
    'problem.sampleTests': 'Casos de Prueba',
    'problem.sample': 'Ejemplo',
    'problem.input': 'Entrada',
    'problem.output': 'Salida Esperada',
    'problem.constraints': 'Restricciones',
    'problem.timeLimit': 'Límite de Tiempo',
    'problem.memoryLimit': 'Límite de Memoria',
    'problem.currentPoints': 'Puntos Actuales',
    'problem.solvedBy': 'Resuelto Por',
    'problem.accuracy': 'Precisión',
    'problem.points': 'puntos',
    'problem.yourSolution': 'Tu Solución',
    'problem.yourCode': 'Tu Código',
    'problem.language': 'Lenguaje',
    'problem.autoSave': 'Auto-guardado activado',
    'problem.toggleTheme': 'Tema',
    'problem.submitCode': 'Enviar Código',
    'problem.resetCode': 'Reiniciar Plantilla',
    'problem.viewEditorial': 'Ver Editorial',
    'problem.editorial': 'Editorial',
    'problem.close': 'Cerrar',
    'problem.submit': 'Enviar Código',
    'problem.reset': 'Reiniciar Código',
    'problem.theme': 'Tema del Editor',
    'problem.themeDark': 'Oscuro',
    'problem.themeLight': 'Claro',
    'problem.submitting': 'Enviando...',
    'problem.submissionReceived': '¡Envío recibido! Evaluando...',
    'problem.recentSubmissions': 'Tus Envíos Recientes',
    'problem.noSubmissions': 'No hay envíos todavía. ¡Envía tu solución para empezar!',

    // Submissions
    'submissions.title': 'Envíos',
    'submissions.description': 'Ve todos tus envíos de código y sus resultados',
    'submissions.id': 'ID',
    'submissions.user': 'Usuario',
    'submissions.problem': 'Problema',
    'submissions.language': 'Lenguaje',
    'submissions.verdict': 'Veredicto',
    'submissions.time': 'Tiempo',
    'submissions.memory': 'Memoria',
    'submissions.submittedAt': 'Enviado',
    'submissions.viewCode': 'Ver Código',
    'submissions.testResults': 'Resultados de Pruebas',
    'submissions.noSubmissions': 'No hay envíos todavía',
    'submissions.noSubmissionsText': 'Comienza a resolver problemas para ver tus envíos aquí',
    'submissions.browsePproblems': 'Explorar Problemas',
    'submissions.filterByVerdict': 'Filtrar por Veredicto',
    'submissions.filterByProblem': 'Filtrar por Problema',
    'submissions.allVerdicts': 'Todos los Veredictos',
    'submissions.allProblems': 'Todos los Problemas',
    'submissions.totalSubmissions': 'Envíos Totales',
    'submissions.accepted': 'Aceptados',
    'submissions.acceptanceRate': 'Tasa de Aceptación',
    'submissions.submissionDetails': 'Detalles del Envío',
    'submissions.submissionId': 'ID de Envío',
    'submissions.sourceCode': 'Código Fuente',

    // Verdicts
    'verdict.AC': 'Aceptado',
    'verdict.WA': 'Respuesta Incorrecta',
    'verdict.TLE': 'Límite de Tiempo Excedido',
    'verdict.MLE': 'Límite de Memoria Excedido',
    'verdict.RE': 'Error de Ejecución',
    'verdict.CE': 'Error de Compilación',
    'verdict.PENDING': 'Pendiente',
    'verdicts.AC': 'Aceptado',
    'verdicts.WA': 'Respuesta Incorrecta',
    'verdicts.TLE': 'Límite de Tiempo Excedido',
    'verdicts.MLE': 'Límite de Memoria Excedido',
    'verdicts.RE': 'Error de Ejecución',
    'verdict.RE': 'Error de Ejecución',
    'verdict.CE': 'Error de Compilación',
    'verdict.PENDING': 'Pendiente',

    // Ranking
    'ranking.title': 'Tabla de Posiciones',
    'ranking.description': 'Mejores jugadores ranqueados por puntaje total',
    'ranking.rank': 'Posición',
    'ranking.username': 'Usuario',
    'ranking.totalScore': 'Puntaje Total',
    'ranking.problemsSolved': 'Problemas Resueltos',
    'ranking.you': 'Tú',
    'ranking.totalUsers': 'Total de Usuarios',
    'ranking.yourRank': 'Tu Posición',
    'ranking.yourScore': 'Tu Puntaje',

    // Admin
    'admin.title': 'Panel de Administración - CodeProof',
    'admin.pageTitle': 'Panel de Administración',
    'admin.subtitle': 'Gestionar usuarios, problemas y configuración del sistema',
    'admin.tabs.users': 'Usuarios',
    'admin.tabs.problems': 'Problemas',
    'admin.tabs.stats': 'Estadísticas',

    // Admin - Pestaña Usuarios
    'admin.users.title': 'Gestión de Usuarios',
    'admin.users.subtitle': 'Gestionar roles y permisos de usuarios',
    'admin.users.search': 'Buscar Usuarios',
    'admin.users.searchPlaceholder': 'Buscar por usuario o correo...',
    'admin.users.filterRole': 'Filtrar por Rol',
    'admin.users.allRoles': 'Todos los Roles',
    'admin.users.results': 'Resultados',
    'admin.users.usersFound': 'usuarios encontrados',
    'admin.users.empty': 'No se encontraron usuarios',
    'admin.users.table.id': 'ID',
    'admin.users.table.username': 'Usuario',
    'admin.users.table.email': 'Correo',
    'admin.users.table.role': 'Rol',
    'admin.users.table.score': 'Puntaje Total',
    'admin.users.table.solved': 'Problemas Resueltos',
    'admin.users.table.createdAt': 'Fecha de Creación',
    'admin.users.table.actions': 'Acciones',
    'admin.users.resetPassword': 'Reiniciar Contraseña',

    // Admin - Pestaña Problemas
    'admin.problems.title': 'Gestión de Problemas',
    'admin.problems.subtitle': 'Revisar y aprobar problemas pendientes',
    'admin.problems.empty': 'No hay problemas pendientes',
    'admin.problems.emptyDesc': 'Todos los problemas han sido revisados',
    'admin.problems.table.id': 'ID',
    'admin.problems.table.title': 'Título',
    'admin.problems.table.difficulty': 'Dificultad',
    'admin.problems.table.createdBy': 'Creado Por',
    'admin.problems.table.createdAt': 'Fecha de Creación',
    'admin.problems.table.status': 'Estado',
    'admin.problems.table.actions': 'Acciones',
    'admin.problems.approve': 'Aprobar',
    'admin.problems.reject': 'Rechazar',
    'admin.problems.detail.difficulty': 'Dificultad',
    'admin.problems.detail.creator': 'Creado por',
    'admin.problems.detail.description': 'Vista Previa de Descripción',

    // Admin - Pestaña Estadísticas
    'admin.stats.title': 'Estadísticas del Sistema',
    'admin.stats.totalUsers': 'Usuarios Totales',
    'admin.stats.totalProblems': 'Problemas Totales',
    'admin.stats.totalSubmissions': 'Envíos Totales',
    'admin.stats.pendingProblems': 'Problemas Pendientes',
    'admin.stats.acSubmissions': 'Envíos Aceptados',
    'admin.stats.acceptanceRate': 'Tasa de Aceptación',
    'admin.stats.recentActivity': 'Actividad Reciente',
    'admin.stats.activeToday': 'Usuarios activos hoy',
    'admin.stats.submissionsToday': 'Envíos de hoy',
    'admin.stats.newUsersWeek': 'Nuevos usuarios esta semana',
    'admin.stats.systemHealth': 'Salud del Sistema',

    // Admin - Modal de Reinicio de Contraseña
    'admin.passwordReset.title': 'Reiniciar Contraseña de Usuario',
    'admin.passwordReset.description': 'Ingresa una nueva contraseña para este usuario. Asegúrate de comunicarla de forma segura.',
    'admin.passwordReset.username': 'Usuario',
    'admin.passwordReset.newPassword': 'Nueva Contraseña',
    'admin.passwordReset.confirmPassword': 'Confirmar Contraseña',
    'admin.passwordReset.passwordHelp': 'Mínimo 8 caracteres',
    'admin.passwordReset.setPassword': 'Establecer Contraseña',
    'admin.passwordReset.warning': '⚠️ Advertencia:',
    'admin.passwordReset.warningText': 'Asegúrate de comunicar esta contraseña de forma segura al usuario.',

    // Problemsetter
    'problemsetter.title': 'Panel de Creador de Problemas - CodeProof',
    'problemsetter.pageTitle': 'Panel de Creador de Problemas',
    'problemsetter.subtitle': 'Crea y gestiona problemas de código para la plataforma',
    'problemsetter.tabs.create': 'Crear Problema',
    'problemsetter.tabs.myProblems': 'Mis Problemas',
    'problemsetter.tabs.submissions': 'Envíos',

    // Problemsetter - Pestaña Crear
    'problemsetter.create.title': 'Crear Nuevo Problema',
    'problemsetter.create.subtitle': 'Completa los detalles a continuación para enviar un nuevo problema a revisión',
    'problemsetter.create.submit': 'Enviar Problema para Revisión',

    // Problemsetter - Pestaña Mis Problemas
    'problemsetter.myProblems.title': 'Mis Problemas',
    'problemsetter.myProblems.subtitle': 'Rastrea el estado de tus problemas enviados',
    'problemsetter.myProblems.filterStatus': 'Filtrar por Estado',
    'problemsetter.myProblems.allStatuses': 'Todos los Estados',
    'problemsetter.myProblems.pending': 'Pendiente',
    'problemsetter.myProblems.approved': 'Aprobado',
    'problemsetter.myProblems.rejected': 'Rechazado',
    'problemsetter.myProblems.empty': 'No se encontraron problemas',
    'problemsetter.myProblems.emptyDesc': '¡Crea tu primer problema para comenzar!',
    'problemsetter.myProblems.table.id': 'ID',
    'problemsetter.myProblems.table.title': 'Título',
    'problemsetter.myProblems.table.difficulty': 'Dificultad',
    'problemsetter.myProblems.table.status': 'Estado',
    'problemsetter.myProblems.table.createdAt': 'Fecha de Creación',
    'problemsetter.myProblems.table.actions': 'Acciones',

    // Problemsetter - Pestaña Envíos
    'problemsetter.submissions.title': 'Envíos a Mis Problemas',
    'problemsetter.submissions.subtitle': 'Ve todos los envíos a tus problemas aprobados',
    'problemsetter.submissions.empty': 'No hay envíos todavía',
    'problemsetter.submissions.emptyDesc': 'Una vez que tus problemas sean aprobados, los envíos aparecerán aquí',
    'problemsetter.submissions.table.user': 'Usuario',

    // Create Problem
    'createProblem.title': 'Crear Problema',
    'createProblem.titleEN': 'Título (Inglés)',
    'createProblem.titleES': 'Título (Español)',
    'createProblem.titleENPlaceholder': 'ej., Hola Bitcoin',
    'createProblem.titleESPlaceholder': 'ej., Hola Bitcoin',
    'createProblem.descriptionEN': 'Descripción (Inglés)',
    'createProblem.descriptionES': 'Descripción (Español)',
    'createProblem.descriptionENPlaceholder': 'Escribe la descripción del problema en markdown...',
    'createProblem.descriptionESPlaceholder': 'Escribe la descripción del problema en markdown...',
    'createProblem.difficulty': 'Dificultad',
    'createProblem.timeLimit': 'Límite de Tiempo (segundos)',
    'createProblem.memoryLimit': 'Límite de Memoria (MB)',
    'createProblem.sampleTests': 'Casos de Prueba de Ejemplo (visibles para usuarios)',
    'createProblem.hiddenTests': 'Casos de Prueba Ocultos (solo para evaluación)',
    'createProblem.addTest': 'Agregar Prueba',
    'createProblem.input': 'Entrada',
    'createProblem.expectedOutput': 'Salida Esperada',
    'createProblem.preview': 'Vista Previa',
    'createProblem.togglePreview': 'Alternar Vista Previa',

    // Notifications
    'notif.loginSuccess': 'Inicio de sesión exitoso',
    'notif.loginError': 'Credenciales inválidas',
    'notif.logoutSuccess': 'Sesión cerrada exitosamente',
    'notif.submitSuccess': 'Código enviado exitosamente',
    'notif.submitError': 'Error al enviar código',
    'notif.saveSuccess': 'Guardado exitosamente',
    'notif.saveError': 'Error al guardar',
    'notif.deleteSuccess': 'Eliminado exitosamente',
    'notif.deleteError': 'Error al eliminar',

    // Errors
    'error.generic': 'Ocurrió un error',
    'error.network': 'Error de red. Por favor verifica tu conexión.',
    'error.unauthorized': 'No estás autorizado para realizar esta acción',
    'error.notFound': 'Recurso no encontrado',
    'error.validation': 'Por favor verifica tu entrada',
    'errors.unauthorized': 'No tienes permiso para acceder a esta página',
    'errors.problemNotFound': 'Problema no encontrado',
    'errors.loadProblemFailed': 'Error al cargar el problema',
    'errors.codeEmpty': 'El código no puede estar vacío',
    'errors.submissionFailed': 'Error al enviar el código',
    'errors.judgingTimeout': 'La evaluación está tomando más tiempo del esperado. Revisa la página de envíos.',

    // Time units
    'time.seconds': '{count}s',
    'time.milliseconds': '{count}ms',
    'time.minutes': '{count}m',
    'time.hours': '{count}h',
    'time.days': '{count}d',
    'time.justNow': 'Justo ahora',
    'time.ago': 'hace {time}',

    // Landing Page - Hero
    'hero.title': 'Demuestra tu Código en el Ecosistema Bitcoin',
    'hero.subtitle': 'Resuelve desafíos de programación sobre Bitcoin y compite globalmente',
    'hero.cta.start': 'Comenzar a Resolver',
    'hero.cta.browse': 'Ver Problemas',
    'hero.stats.submissions': 'Envíos',
    'hero.stats.users': 'Usuarios',
    'hero.stats.blocks': 'Bloques Minados',
    'hero.stats.problems': 'Problemas',

    // Landing Page - Features
    'features.title': '¿Por qué CodeProof?',
    'features.dynamic.title': 'Puntuación Dinámica',
    'features.dynamic.desc': 'Los puntos de los problemas disminuyen conforme más usuarios los resuelven, recompensando a los primeros',
    'features.learn.title': 'Aprende Bitcoin',
    'features.learn.desc': 'Domina conceptos de Bitcoin a través de desafíos de programación prácticos',
    'features.compete.title': 'Compite Globalmente',
    'features.compete.desc': 'Escala en el ranking y demuestra tus habilidades contra desarrolladores de todo el mundo',

    // Landing Page - How It Works
    'howItWorks.title': 'Cómo Funciona',
    'howItWorks.step1.title': 'Elige un Problema',
    'howItWorks.step1.desc': 'Explora desafíos de código sobre Bitcoin',
    'howItWorks.step2.title': 'Programa y Prueba',
    'howItWorks.step2.desc': 'Escribe y prueba tu solución contra casos de ejemplo',
    'howItWorks.step3.title': 'Envía tu Código',
    'howItWorks.step3.desc': 'Evaluación automática en tiempo real',
    'howItWorks.step4.title': 'Gana Puntos y Sube en el Ranking',
    'howItWorks.step4.desc': 'Tu solución aceptada suma puntos y otros usuarios la ven',
    'howItWorks.step5.title': 'Registrado en Bloques Cada 10 Min',
    'howItWorks.step5.desc': 'Las soluciones se graban en bloques. El primer usuario en resolver cada problema es el "minero" del bloque',

    // Landing Page - Leaderboard
    'leaderboard.title': 'Mejores Jugadores',
    'leaderboard.viewAll': 'Ranking Completo →',

    // Landing Page - Footer
    'footer.platform': 'Plataforma',
    'footer.problems': 'Problemas',
    'footer.blocks': 'Blockchain',
    'footer.ranking': 'Ranking',
    'footer.login': 'Iniciar Sesión',
    'footer.resources': 'Recursos',
    'footer.docs': 'Documentación',
    'footer.api': 'API',
    'footer.github': 'GitHub',
    'footer.howItWorks': 'Cómo Funciona',
    'footer.legal': 'Legal',
    'footer.about': 'Acerca de',
    'footer.contact': 'Contacto',
    'footer.terms': 'Términos de Servicio',
    'footer.privacy': 'Política de Privacidad',
  }
};

/**
 * Get translation for a key
 *
 * @param {string} key - Translation key (e.g., 'auth.login' or 'quickLinks.problems.title')
 * @param {object} params - Optional parameters for string interpolation
 * @returns {string} Translated string
 */
function t(key, params = {}) {
  const lang = translations[currentLanguage] || translations.en;

  // First try direct key lookup (for backward compatibility)
  let text = lang[key];

  // If not found, try nested key lookup (e.g., 'quickLinks.problems.title')
  if (text === undefined) {
    const keys = key.split('.');
    text = keys.reduce((obj, k) => (obj && obj[k] !== undefined) ? obj[k] : undefined, lang);
  }

  // If still not found, return the key itself
  if (text === undefined) {
    text = key;
  }

  // Replace parameters like {username}, {count}, etc.
  Object.keys(params).forEach(param => {
    text = text.replace(new RegExp(`\\{${param}\\}`, 'g'), params[param]);
  });

  return text;
}

/**
 * Switch language and update all elements with data-i18n attribute
 *
 * @param {string} lang - Language code ('en' or 'es')
 */
function switchLanguage(lang) {
  if (!translations[lang]) {
    console.warn(`Language '${lang}' not supported`);
    return;
  }

  currentLanguage = lang;

  // Save to localStorage
  localStorage.setItem('codeproof_language', lang);

  // Update all elements with data-i18n attribute
  updateI18nElements();

  // Dispatch event for components to react to language change
  document.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lang } }));
}

/**
 * Update all elements with data-i18n attribute
 */
function updateI18nElements() {
  const elements = document.querySelectorAll('[data-i18n]');
  elements.forEach(element => {
    const key = element.getAttribute('data-i18n');
    const params = element.dataset.i18nParams ? JSON.parse(element.dataset.i18nParams) : {};
    element.textContent = t(key, params);
  });

  // Update placeholders
  const placeholders = document.querySelectorAll('[data-i18n-placeholder]');
  placeholders.forEach(element => {
    const key = element.getAttribute('data-i18n-placeholder');
    element.setAttribute('placeholder', t(key));
  });
}

/**
 * Get current language
 *
 * @returns {string} Current language code
 */
function getCurrentLanguage() {
  return currentLanguage;
}

/**
 * Initialize i18n system
 * Loads saved language from localStorage
 */
function initI18n() {
  // Load saved language
  const savedLang = localStorage.getItem('codeproof_language');
  if (savedLang && translations[savedLang]) {
    currentLanguage = savedLang;
  }

  // Update elements on page load
  updateI18nElements();
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initI18n);
} else {
  initI18n();
}

// Export public API
window.i18n = {
  t: t,
  setLanguage: switchLanguage,
  getCurrentLanguage: getCurrentLanguage,
  updateElements: updateI18nElements,
  get currentLang() {
    return currentLanguage;
  },
  addTranslations: function(newTranslations) {
    // Merge new translations (deep merge for each language)
    Object.keys(newTranslations).forEach(lang => {
      if (translations[lang]) {
        Object.assign(translations[lang], newTranslations[lang]);
      }
    });
    // Update elements after adding translations
    updateI18nElements();
  }
};
