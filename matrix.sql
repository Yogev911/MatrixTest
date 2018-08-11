-- phpMyAdmin SQL Dump
-- version 4.7.7
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Mar 18, 2018 at 06:22 PM
-- Server version: 10.1.30-MariaDB
-- PHP Version: 5.6.33

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `matrix`
--

-- --------------------------------------------------------

--
-- Table structure for table `doc_tbl`
--

CREATE TABLE `doc_tbl` (
  `docid` int(11) NOT NULL,
  `docname` varchar(250) NOT NULL,
  `author` varchar(250) NOT NULL,
  `path` varchar(250) NOT NULL,
  `year` varchar(250) NOT NULL,
  `intro` varchar(250) NOT NULL,
  `hidden` int(11) NOT NULL,
  `url` varchar(1023) NOT NULL

) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `hidden_files`
--

CREATE TABLE `hidden_files` (
  `docid` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `indextable`
--

CREATE TABLE `indextable` (
  `postid` int(11) NOT NULL,
  `term` varchar(30) NOT NULL,
  `hit` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `postfiletable`
--

CREATE TABLE `postfiletable` (
  `id` int(11) NOT NULL,
  `postid` int(11) NOT NULL,
  `hit` int(11) DEFAULT NULL,
  `docid` int(30) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `doc_tbl`
--
ALTER TABLE `doc_tbl`
  ADD PRIMARY KEY (`docid`);

--
-- Indexes for table `indextable`
--
ALTER TABLE `indextable`
  ADD PRIMARY KEY (`postid`);

--
-- Indexes for table `postfiletable`
--
ALTER TABLE `postfiletable`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `doc_tbl`
--
ALTER TABLE `doc_tbl`
  MODIFY `docid` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `indextable`
--
ALTER TABLE `indextable`
  MODIFY `postid` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `postfiletable`
--
ALTER TABLE `postfiletable`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
