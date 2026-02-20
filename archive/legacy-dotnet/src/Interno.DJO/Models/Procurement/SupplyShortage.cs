using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.DJO.Models
{
    public class SupplyShortage
    {
        [Key]
        public int Id { get; set; }
        public string Supplier { get; set; }
        public string Buyer { get; set; }
        public string CategoryManager { get; set; }
        public SupplyIssueType IssueType { get; set; }
        public string PartNumber { get; set; }
        public DateTime StockOutDate { get; set; }
        public decimal BackOrder { get; set; }
        public string CurrentUpdate { get; set; }
        public string RootCause { get; set; }
        public Site Site { get; set; }
        public string ProductInpact { get; set; }
        public DateTime ExpectedClose { get; set; }
        public string RoouCauseDetails { get; set; }
        
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.Now;
        [TimestampAttribute]
        [DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        public DateTime Updated { get; set; } = DateTime.Now;  

        public virtual string Category { get; set; }
        public virtual double DaysAgging { get{ return (DateTime.Now - Created).TotalDays;} }
    }

    public enum SupplyIssueType
    {
        Major,
        Moderate,
        Minor,
        Monitor
    }

    
    
}