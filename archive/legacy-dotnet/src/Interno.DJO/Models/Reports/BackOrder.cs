using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace Interno.DJO.Models
{
    public class BackOrder
    {
        [Key]
        public int Id { get; set; }
        public DateTime Date { get; set; }
        public string Item { get; set; }
        public double Quantity { get; set; }
        public double Amount { get; set; }
        public double BOMAffectedAmount { get; set; }
        public virtual ICollection<BOM> BOM { get; set; }

    }
    public class BackOrderTrend
    {
        [Key]
        public int Id { get; set; }
        public DateTime Date { get; set; }
        public decimal Backlog { get; set; }
        public decimal BackOrder { get; set; }
        public decimal OpenOrder { get; set; }
    }
}