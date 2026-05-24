-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: May 24, 2026 at 07:34 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `face_attendance_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `absence_records`
--

CREATE TABLE `absence_records` (
  `id` int(11) NOT NULL,
  `student_id` int(11) NOT NULL,
  `lecture_id` int(11) NOT NULL,
  `faculty_id` int(11) NOT NULL,
  `absence_date` date NOT NULL,
  `reason` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `attendance`
--

CREATE TABLE `attendance` (
  `id` int(11) NOT NULL,
  `student_id` int(11) NOT NULL,
  `lecture_id` int(11) NOT NULL,
  `faculty_id` int(11) NOT NULL,
  `attendance_time` timestamp NOT NULL DEFAULT current_timestamp(),
  `status` enum('Present','Absent') DEFAULT 'Present',
  `is_locked` tinyint(1) DEFAULT 0,
  `last_modified` timestamp NOT NULL DEFAULT current_timestamp(),
  `confidence` decimal(5,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `attendance`
--

INSERT INTO `attendance` (`id`, `student_id`, `lecture_id`, `faculty_id`, `attendance_time`, `status`, `is_locked`, `last_modified`, `confidence`) VALUES
(9, 1, 3, 1, '2025-10-15 12:48:57', 'Present', 0, '2025-10-15 12:48:57', NULL),
(12, 1, 3, 1, '2025-10-30 15:49:03', 'Present', 0, '2025-10-30 15:49:03', NULL),
(16, 2, 3, 1, '2025-11-01 12:29:41', 'Absent', 0, '2025-11-01 12:29:41', NULL),
(21, 2, 3, 1, '2025-11-02 11:38:51', 'Absent', 0, '2025-11-02 11:38:51', NULL),
(24, 1, 5, 2, '2025-11-02 12:11:31', 'Absent', 0, '2025-11-02 12:11:31', NULL),
(25, 2, 5, 2, '2025-11-02 12:11:31', 'Absent', 0, '2025-11-02 12:11:31', NULL),
(27, 1, 5, 2, '2025-11-06 13:56:24', 'Absent', 0, '2025-11-06 13:56:24', NULL),
(28, 2, 5, 2, '2025-11-06 13:56:24', 'Absent', 0, '2025-11-06 13:56:24', NULL),
(31, 1, 5, 2, '2025-11-11 17:37:52', 'Present', 0, '2025-11-11 17:37:52', NULL),
(32, 2, 5, 2, '2025-11-11 17:38:12', 'Absent', 0, '2025-11-11 17:38:12', NULL),
(33, 2, 5, 2, '2025-11-13 11:37:23', 'Absent', 0, '2025-11-13 11:37:23', NULL),
(34, 2, 5, 2, '2025-11-13 11:37:29', 'Absent', 0, '2025-11-13 11:37:29', NULL),
(35, 1, 5, 2, '2025-11-13 11:38:20', 'Present', 0, '2025-11-13 11:38:20', NULL),
(36, 1, 6, 2, '2025-11-13 11:38:58', 'Absent', 0, '2025-11-13 11:38:58', NULL),
(37, 2, 6, 2, '2025-11-13 11:38:58', 'Absent', 0, '2025-11-13 11:38:58', NULL),
(38, 2, 5, 2, '2025-11-13 11:39:07', 'Absent', 0, '2025-11-13 11:39:07', NULL),
(39, 1, 3, 1, '2025-11-13 14:39:03', 'Present', 0, '2025-11-13 14:39:03', NULL),
(40, 1, 3, 1, '2025-11-14 13:18:01', 'Present', 0, '2025-11-14 13:18:01', NULL),
(41, 1, 3, 1, '2025-11-16 09:25:34', 'Present', 0, '2025-11-16 09:25:34', NULL),
(42, 2, 3, 1, '2025-11-16 15:23:20', 'Absent', 0, '2025-11-16 15:23:20', NULL),
(43, 2, 3, 1, '2025-11-16 17:41:56', 'Absent', 0, '2025-11-16 17:41:56', NULL),
(44, 1, 5, 2, '2025-11-16 17:43:09', 'Present', 0, '2025-11-16 17:43:09', NULL),
(45, 1, 6, 2, '2025-11-16 17:43:36', 'Absent', 0, '2025-11-16 17:43:36', NULL),
(46, 2, 6, 2, '2025-11-16 17:43:36', 'Absent', 0, '2025-11-16 17:43:36', NULL),
(47, 1, 5, 2, '2025-11-19 08:52:07', 'Present', 0, '2025-11-19 08:52:07', NULL),
(48, 2, 5, 2, '2025-11-21 13:26:28', 'Absent', 0, '2025-11-21 13:26:28', NULL),
(49, 2, 5, 2, '2025-11-21 13:26:40', 'Absent', 0, '2025-11-21 13:26:40', NULL),
(50, 1, 6, 2, '2025-11-21 13:26:49', 'Absent', 0, '2025-11-21 13:26:49', NULL),
(51, 2, 6, 2, '2025-11-21 13:26:49', 'Absent', 0, '2025-11-21 13:26:49', NULL),
(52, 2, 5, 2, '2025-11-21 13:27:08', 'Absent', 0, '2025-11-21 13:27:08', NULL),
(53, 2, 3, 1, '2025-11-26 12:00:18', 'Absent', 0, '2025-11-26 12:00:18', NULL),
(54, 4, 3, 1, '2025-11-26 12:00:18', 'Absent', 0, '2025-11-26 12:00:18', NULL),
(55, 1, 3, 1, '2025-11-26 19:32:47', 'Present', 0, '2025-11-26 19:32:47', NULL),
(56, 2, 3, 1, '2025-11-27 13:29:18', 'Absent', 0, '2025-11-27 13:29:18', NULL),
(57, 4, 3, 1, '2025-11-27 13:29:18', 'Absent', 0, '2025-11-27 13:29:18', NULL),
(58, 2, 3, 1, '2025-11-27 13:36:52', 'Absent', 0, '2025-11-27 13:36:52', NULL),
(59, 4, 3, 1, '2025-11-27 13:36:52', 'Absent', 0, '2025-11-27 13:36:52', NULL),
(60, 2, 3, 1, '2025-11-27 13:36:58', 'Absent', 0, '2025-11-27 13:36:58', NULL),
(61, 4, 3, 1, '2025-11-27 13:36:58', 'Absent', 0, '2025-11-27 13:36:58', NULL),
(62, 1, 3, 1, '2025-11-28 07:33:47', 'Present', 0, '2025-11-28 07:33:47', NULL),
(63, 1, 7, 1, '2025-11-28 07:43:52', 'Present', 0, '2025-11-28 07:43:52', NULL),
(64, 2, 3, 1, '2025-11-28 07:49:52', 'Absent', 0, '2025-11-28 07:49:52', NULL),
(65, 4, 3, 1, '2025-11-28 07:49:52', 'Absent', 0, '2025-11-28 07:49:52', NULL),
(66, 2, 7, 1, '2025-12-09 14:16:13', 'Present', 0, '2025-12-09 14:16:13', NULL),
(67, 1, 7, 1, '2025-12-09 14:16:33', 'Present', 0, '2025-12-09 14:16:33', NULL),
(68, 1, 3, 1, '2025-12-09 14:42:16', 'Present', 0, '2025-12-09 14:42:16', NULL),
(69, 1, 7, 1, '2025-12-10 04:45:18', 'Present', 0, '2025-12-10 04:45:18', NULL),
(70, 2, 3, 1, '2025-12-10 08:56:59', 'Absent', 0, '2025-12-10 08:56:59', NULL),
(71, 4, 3, 1, '2025-12-10 08:56:59', 'Absent', 0, '2025-12-10 08:56:59', NULL),
(72, 5, 3, 1, '2025-12-10 08:56:59', 'Absent', 0, '2025-12-10 08:56:59', NULL),
(73, 1, 3, 1, '2025-12-10 09:39:22', 'Present', 0, '2025-12-10 09:39:22', NULL),
(74, 2, 3, 1, '2025-12-10 09:41:05', 'Absent', 0, '2025-12-10 09:41:05', NULL),
(75, 4, 3, 1, '2025-12-10 09:41:05', 'Absent', 0, '2025-12-10 09:41:05', NULL),
(76, 5, 3, 1, '2025-12-10 09:41:05', 'Absent', 0, '2025-12-10 09:41:05', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `faculty`
--

CREATE TABLE `faculty` (
  `id` int(11) NOT NULL,
  `faculty_id` varchar(20) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `faculty`
--

INSERT INTO `faculty` (`id`, `faculty_id`, `name`, `email`, `password`, `created_at`) VALUES
(1, 'F1', 'pankti', 'pankti@gmail.com', '0911', '2025-09-02 17:04:51'),
(2, 'F2', 'hetvi', 'hetvi@gmail.com', '123', '2025-09-02 17:04:51'),
(3, 'f3', 'neha prajapati', 'neha123@gmail.com', 'scrypt:32768:8:1$fGXZSFzWjidP2HEe$762b2a1e7061a3faf353ea804018837820828ceef9a00f4384aa386d5affcbfb990661767d8aafcaf3bce3b0a391b59a8df33471da9229bfee089fcd99b538cd', '2025-11-26 20:13:09');

-- --------------------------------------------------------

--
-- Table structure for table `lectures`
--

CREATE TABLE `lectures` (
  `id` int(11) NOT NULL,
  `lecture_code` varchar(20) NOT NULL,
  `title` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `lectures`
--

INSERT INTO `lectures` (`id`, `lecture_code`, `title`, `description`, `created_at`) VALUES
(3, 'advance java', 'advance', 'djvbfjkdv', '2025-10-15 12:40:29'),
(5, '003', 'php', 'qacddgfg', '2025-11-02 12:11:09'),
(6, 'java', 'jhdj', 'nbdm', '2025-11-13 11:38:47'),
(7, '01', 'AI', 'basics for students\r\n', '2025-11-28 07:41:53');

-- --------------------------------------------------------

--
-- Table structure for table `lecture_faculty`
--

CREATE TABLE `lecture_faculty` (
  `id` int(11) NOT NULL,
  `lecture_id` int(11) NOT NULL,
  `faculty_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `lecture_faculty`
--

INSERT INTO `lecture_faculty` (`id`, `lecture_id`, `faculty_id`) VALUES
(3, 3, 1),
(5, 5, 2),
(6, 6, 2),
(7, 7, 1);

-- --------------------------------------------------------

--
-- Table structure for table `lecture_students`
--

CREATE TABLE `lecture_students` (
  `id` int(11) NOT NULL,
  `lecture_id` int(11) NOT NULL,
  `student_id` int(11) NOT NULL,
  `enrolled_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `password_reset_tokens`
--

CREATE TABLE `password_reset_tokens` (
  `id` int(11) NOT NULL,
  `faculty_id` int(11) NOT NULL,
  `token` varchar(255) NOT NULL,
  `expires_at` datetime NOT NULL,
  `used` tinyint(1) DEFAULT 0,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `password_reset_tokens`
--

INSERT INTO `password_reset_tokens` (`id`, `faculty_id`, `token`, `expires_at`, `used`, `created_at`) VALUES
(2, 1, '-fBAHlYKoiCl8VQWJaP4aY8Ouew4ki2LfK-9WIRsY10', '2025-10-15 19:48:21', 0, '2025-10-15 13:18:21');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `student_id` varchar(20) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `photo_path` varchar(255) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `student_id`, `name`, `email`, `photo_path`, `created_at`) VALUES
(1, '4076', 'pankti prajapati', 'pankti0911@gmail.com', '4076_20250902_222649.jpg', '2025-09-02 16:56:49'),
(2, '4033', 'ranjan prajapati', 'ranjan11@gmail.com', '4033_20251030_211836.jpg', '2025-10-30 15:48:36'),
(4, 'p1', 'sbd ehfj', 'kgfpatel75@gmail.com', 'p1_20251121_194323.jpg', '2025-11-21 14:13:23'),
(5, '4688', 'hdbcmhfb', '12@hgshsg.com', '4688_20251210_132508.jpg', '2025-12-10 07:55:08');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `absence_records`
--
ALTER TABLE `absence_records`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_absence_record` (`student_id`,`lecture_id`,`absence_date`),
  ADD KEY `lecture_id` (`lecture_id`),
  ADD KEY `faculty_id` (`faculty_id`);

--
-- Indexes for table `attendance`
--
ALTER TABLE `attendance`
  ADD PRIMARY KEY (`id`),
  ADD KEY `student_id` (`student_id`),
  ADD KEY `lecture_id` (`lecture_id`),
  ADD KEY `faculty_id` (`faculty_id`);

--
-- Indexes for table `faculty`
--
ALTER TABLE `faculty`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `faculty_id` (`faculty_id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `lectures`
--
ALTER TABLE `lectures`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `lecture_code` (`lecture_code`);

--
-- Indexes for table `lecture_faculty`
--
ALTER TABLE `lecture_faculty`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_lecture_faculty` (`lecture_id`,`faculty_id`),
  ADD KEY `faculty_id` (`faculty_id`);

--
-- Indexes for table `lecture_students`
--
ALTER TABLE `lecture_students`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_lecture_student` (`lecture_id`,`student_id`),
  ADD KEY `student_id` (`student_id`);

--
-- Indexes for table `password_reset_tokens`
--
ALTER TABLE `password_reset_tokens`
  ADD PRIMARY KEY (`id`),
  ADD KEY `faculty_id` (`faculty_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `student_id` (`student_id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `absence_records`
--
ALTER TABLE `absence_records`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `attendance`
--
ALTER TABLE `attendance`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=77;

--
-- AUTO_INCREMENT for table `faculty`
--
ALTER TABLE `faculty`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `lectures`
--
ALTER TABLE `lectures`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `lecture_faculty`
--
ALTER TABLE `lecture_faculty`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `lecture_students`
--
ALTER TABLE `lecture_students`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `password_reset_tokens`
--
ALTER TABLE `password_reset_tokens`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `absence_records`
--
ALTER TABLE `absence_records`
  ADD CONSTRAINT `absence_records_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `absence_records_ibfk_2` FOREIGN KEY (`lecture_id`) REFERENCES `lectures` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `absence_records_ibfk_3` FOREIGN KEY (`faculty_id`) REFERENCES `faculty` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `attendance`
--
ALTER TABLE `attendance`
  ADD CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `attendance_ibfk_2` FOREIGN KEY (`lecture_id`) REFERENCES `lectures` (`id`),
  ADD CONSTRAINT `attendance_ibfk_3` FOREIGN KEY (`faculty_id`) REFERENCES `faculty` (`id`);

--
-- Constraints for table `lecture_faculty`
--
ALTER TABLE `lecture_faculty`
  ADD CONSTRAINT `lecture_faculty_ibfk_1` FOREIGN KEY (`lecture_id`) REFERENCES `lectures` (`id`),
  ADD CONSTRAINT `lecture_faculty_ibfk_2` FOREIGN KEY (`faculty_id`) REFERENCES `faculty` (`id`);

--
-- Constraints for table `lecture_students`
--
ALTER TABLE `lecture_students`
  ADD CONSTRAINT `lecture_students_ibfk_1` FOREIGN KEY (`lecture_id`) REFERENCES `lectures` (`id`),
  ADD CONSTRAINT `lecture_students_ibfk_2` FOREIGN KEY (`student_id`) REFERENCES `users` (`id`);

--
-- Constraints for table `password_reset_tokens`
--
ALTER TABLE `password_reset_tokens`
  ADD CONSTRAINT `password_reset_tokens_ibfk_1` FOREIGN KEY (`faculty_id`) REFERENCES `faculty` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
