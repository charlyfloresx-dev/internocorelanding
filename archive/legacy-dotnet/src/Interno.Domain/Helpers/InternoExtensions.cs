using System;
using System.IO;
using System.Data;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Reflection;
using CsvHelper;
using ExcelDataReader;
using System.Text.RegularExpressions;

namespace Interno.Domain.Helpers
{
    public static partial class InternoExtensions
    {
        static CultureInfo provider = CultureInfo.InvariantCulture;
        public static DateTime FirstDayOfWeek(DateTime date)
        {
            DayOfWeek fdow = CultureInfo.CurrentCulture.DateTimeFormat.FirstDayOfWeek;
            int offset = fdow - date.DayOfWeek;
            DateTime fdowDate = date.AddDays(offset);
            return fdowDate;
        }
        public static DateTime LastDayOfWeek(DateTime date) => FirstDayOfWeek(date).AddDays(6);
        public static DateTime GetLastDayOfMonth(this DateTime dateTime) => new DateTime(dateTime.Year, dateTime.Month, DateTime.DaysInMonth(dateTime.Year, dateTime.Month));

        //* Regresa el numero de Semana en el Mes
        public static int WeekOfMonth(this DateTime date)
        {
            DateTime beginningOfMonth = new DateTime(date.Year, date.Month, 1);
            while (date.Date.AddDays(1).DayOfWeek != CultureInfo.CurrentCulture.DateTimeFormat.FirstDayOfWeek) date = date.AddDays(1);
            return (int)Math.Truncate((double)date.Subtract(beginningOfMonth).TotalDays / 7f) + 1;
        }
        //* Regresa el numero de Semana del año
        public static int WeekOfYear(this DateTime time)
        {
            DayOfWeek day = CultureInfo.InvariantCulture.Calendar.GetDayOfWeek(time);
            if (day >= DayOfWeek.Monday && day <= DayOfWeek.Wednesday) { time = time.AddDays(3); }
            // Return the week of our adjusted day
            return CultureInfo.InvariantCulture.Calendar.GetWeekOfYear(time, CalendarWeekRule.FirstFourDayWeek, DayOfWeek.Monday);
        }
        public static int GetQuarter(this DateTime date)
        {
            if (date.Month >= 4 && date.Month <= 6) return 1;
            else if (date.Month >= 7 && date.Month <= 9) return 2;
            else if (date.Month >= 10 && date.Month <= 12) return 3;
            else return 4;
        }
        public static int getNumber(this string num) => Int32.Parse(Regex.Match(num, @"\d+").Value);

        //DataTable a Lista
        public static List<T> ConvertDataTable<T>(DataTable dt)
        {
            List<T> data = new List<T>();
            foreach (DataRow row in dt.Rows)
            {
                T item = GetItem<T>(row);
                data.Add(item);
            }
            return data;
        }
        private static T GetItem<T>(DataRow dr)
        {
            Type temp = typeof(T);
            T obj = Activator.CreateInstance<T>();

            foreach (DataColumn column in dr.Table.Columns)
            {
                foreach (PropertyInfo pro in temp.GetProperties())
                {
                    if (pro.Name == column.ColumnName)
                        pro.SetValue(obj, dr[column.ColumnName], null);
                    else
                        continue;
                }
            }
            return obj;
        }
        public static DataTableCollection ExcelToDataTable(Stream stream)
        {
            System.Text.Encoding.RegisterProvider(System.Text.CodePagesEncodingProvider.Instance);
            using (var reader = ExcelReaderFactory.CreateReader(stream))
            {
                var result = reader.AsDataSet(new ExcelDataSetConfiguration()
                {
                    ConfigureDataTable = (data) => new ExcelDataTableConfiguration() { UseHeaderRow = true }
                });
                return result.Tables;
            }
        }
        public static DataTable CSVtoDataTable(Stream stream)
        {
            using (var reader = new StreamReader(stream))
            {
                using (var csv = new CsvReader(reader, CultureInfo.InvariantCulture))
                {
                    using (var dr = new CsvDataReader(csv))
                    {
                        var dt = new DataTable();
                        dt.Load(dr);
                        return dt;
                    }
                }
            }
        }
    }
    // public static class ContextExtensions
    // {  
    //     public static void AddOrUpdate(this DbContext ctx, object entity)  
    //     {  
    //         var entry = ctx.Entry(entity);  
    //         switch (entry.State)  
    //         {  
    //             case EntityState.Detached: ctx.Update(entity); break;  
    //             case EntityState.Modified: ctx.Update(entity); break;  
    //             case EntityState.Added: ctx.Add(entity); break; 
    //             case EntityState.Unchanged: break;
    //             default:  
    //                 throw new ArgumentOutOfRangeException();  
    //         }
    //     }
    // }
}