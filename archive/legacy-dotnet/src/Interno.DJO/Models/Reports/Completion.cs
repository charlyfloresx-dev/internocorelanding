using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
namespace Interno.DJO.Models
{
    public class Completion
    {
        public int Id { get; set; }
        public DateTime TransDateTime { get; set; }
        public string JobNumber { get; set; }
        public string Item { get; set; }
        public string Description { get; set; }
        public string ItemType { get; set; }
        public decimal Qty { get; set; }
        public string Module { get; set; }
        public string ModuleDesc { get; set; }
        public string ProductBrand { get; set; }
        public string ValueStream { get; set; }
    }
}
