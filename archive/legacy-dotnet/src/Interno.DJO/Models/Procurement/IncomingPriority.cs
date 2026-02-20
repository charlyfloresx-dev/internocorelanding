using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.DJO.Models
{
    public class IncomingPriority
    {   
        [Key]
        public int Id { get; set; }
        public int Priority { get; set; }
        public string Item { get; set; }
        public string Buyer { get; set; }
        public string Supplier { get; set; }
        public string Reference { get; set; }
        public DateTime ETA { get; set; }
        public string ModuleAffec { get; set; }
        public DateTime ProdInpac { get; set; }
        public string Routing { get; set; }
        public string Comment { get; set; }
        public bool Available { get; set; }
        public DateTime? AvailableDate { get; set; }
        public string CreatedUser { get; set; }
        public string UpdatedUser { get; set; }
        //
        public virtual ICollection<Interno.DJO.Models.DJOLog> Log { get; set; }

        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.Now;
        [TimestampAttribute]
        [DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        public DateTime Updated { get; set; } = DateTime.Now;
        public virtual int Aging {get{return Int16.Parse((DateTime.Now.Date - Created.Date).TotalDays.ToString());}}

        public IncomingPriority(){}
        public IncomingPriority(IFormPriorityLog form)
        {
            Item = form.PO.Item;
            Buyer = form.PO.Buyer;
            Supplier = form.PO.Supplier;
            Routing = form.PO.ReceiptRouting;
            ModuleAffec = form.Affected;
            ProdInpac = form.ProdInpac;
            ETA = form.ETA;
            Reference = form.Reference;
            Priority = form.Priority;
            Comment = form.Comment;
        }
    }

    public class IFormPriorityLog
    {
        [Required]
        public Interno.DJO.Models.PurchaseOrder PO { get; set; }
        [Required]
        public string Reference { get; set; }
        [Required]
        public DateTime ETA { get; set; }
        public string Affected { get; set; }
        public DateTime ProdInpac { get; set; }
        public int Priority { get; set; }
        public string Comment { get; set; }
    }
}