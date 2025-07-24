Ext.define('SYNO.Changepanelsize.MainPanel', {
    extend: 'SYNO.ux.Panel',
    
    constructor: function(config) {
        var me = this;
        
        me.hddBayStore = Ext.create('Ext.data.Store', {
            fields: ['value', 'text'],
            data: [
                {value: 'RACK_0_Bay', text: 'RACK_0_Bay'},
                {value: 'RACK_2_Bay', text: 'RACK_2_Bay'},
                {value: 'RACK_4_Bay', text: 'RACK_4_Bay'},
                // ... 나머지 옵션들
            ]
        });
        
        var panelConfig = {
            items: [{
                xtype: 'form',
                itemId: 'changePanelForm',
                padding: 20,
                items: [{
                    xtype: 'combo',
                    fieldLabel: 'HDD Bay',
                    name: 'hdd_bay',
                    store: me.hddBayStore,
                    displayField: 'text',
                    valueField: 'value',
                    editable: false
                }, {
                    xtype: 'textfield',
                    fieldLabel: 'SSD Bay',
                    name: 'ssd_bay',
                    regex: /^\d+X\d+$/,
                    regexText: 'SSD Bay format should be like: 2X1, 4X2 etc.'
                }],
                buttons: [{
                    text: _T('common', 'apply'),
                    handler: me.onApply,
                    scope: me
                }]
            }]
        };
        
        Ext.apply(config, panelConfig);
        me.callParent([config]);
    },
    
    onApply: function() {
        var me = this;
        var form = me.down('#changePanelForm').getForm();
        
        if (form.isValid()) {
            var values = form.getValues();
            
            Ext.Ajax.request({
                url: 'http://192.168.45.72:8089/Changepanelsize/api',
                method: 'POST',
                jsonData: values,
                success: function(response) {
                    var result = Ext.decode(response.responseText);
                    if (result.success) {
                        SYNO.ux.NotificationMgr.fireInfo({
                            text: result.message
                        });
                    } else {
                        SYNO.ux.NotificationMgr.fireError({
                            text: result.message
                        });
                    }
                },
                failure: function() {
                    SYNO.ux.NotificationMgr.fireError({
                        text: 'Network error occurred'
                    });
                }
            });
        }
    }
});

Ext.define('SYNO.Changepanelsize.Application', {
    extend: 'SYNO.PageApplication',
    
    appWindowName: 'SYNO.Changepanelsize.MainPanel',
    
    constructor: function() {
        this.callParent(arguments);
    }
});

